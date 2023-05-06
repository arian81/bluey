import discord
from sqlalchemy import String, create_engine, Column, DateTime, Boolean, BigInteger, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
import logging
from sqlalchemy.exc import IntegrityError
from discord.ext import commands
from dotenv import load_dotenv
import os

ROLE = 1103847982836744273
load_dotenv()

logging.basicConfig(filename="logs.txt", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


# SQLAlchemy database connection setup
engine = create_engine(os.getenv("DEV_DATABASE_URL"), echo=True)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


# SQLAlchemy Member model
class Member(Base):
    __tablename__ = "members"
    discord_id = Column(BigInteger, primary_key=True)
    discord_username = Column(String, nullable=False)
    join_date = Column(DateTime, nullable=False)
    is_vip = Column(Boolean, nullable=False)
    is_resumecv = Column(Boolean, nullable=False)
    is_invited = Column(Boolean, nullable=False)
    message_count = Column(BigInteger, nullable=False)


Base.metadata.create_all(engine)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print("Locked and loaded!")


@bot.slash_command(
    name="init",
    description="Initialize the database with all the members in the server",
)
async def init(ctx):
    members = ctx.guild.members
    admin_found = False

    for role in ctx.author.roles:
        if role.id == ROLE:
            admin_found = True
            members = ctx.guild.members
            for member in members:
                session = Session()
                join_date = member.joined_at
                new_member = Member(
                    discord_id=member.id,
                    join_date=join_date,
                    discord_username=member.name + member.discriminator,
                    is_vip=False,
                    is_resumecv=False,
                    is_invited=False,
                    message_count=0,
                )
                try:
                    session.add(new_member)
                    session.commit()
                except IntegrityError:
                    session.rollback()
                session.close()
            await ctx.send_response("Database initialized")
    logging.debug(f"{ctx.author.name} initialized the database")

    if admin_found is False:
        await ctx.send_response("You don't have permission to do that")


@bot.slash_command(name="vip", description="Add a member to the VIP list")
async def vip(ctx, member: discord.Member, enable: bool):
    admin_found = False
    for role in ctx.author.roles:
        if role.id == ROLE:
            admin_found = True
            session = Session()
            member = session.query(Member).filter(Member.discord_id == member.id).first()
            member.is_vip = enable
            session.commit()
            if enable:
                await ctx.send_response(f"{member.discord_username} added to VIP list")
            else:
                await ctx.send_response(f"{member.discord_username} removed from VIP list")
            logging.debug(f"{ctx.author.name} added {member.discord_username} to VIP list")
            session.close()
    if admin_found is False:
        await ctx.send_response("You don't have permission to do that")


@bot.slash_command(name="resumecv", description="Add a member to the resume.cv list")
async def resumecv(ctx, member: discord.Member, enable: bool):
    admin_found = False
    for role in ctx.author.roles:
        if role.id == ROLE:
            admin_found = True
            session = Session()
            member = session.query(Member).filter(Member.discord_id == member.id).first()
            member.is_resumecv = enable
            session.commit()
            if enable:
                await ctx.send_response(f"{member.discord_username} added to resume.cv list")
            else:
                await ctx.send_response(f"{member.discord_username} removed from resume.cv list")
            logging.debug(f"{ctx.author.name} added {member.discord_username} to resume.cv list")
            session.close()
    if admin_found is False:
        await ctx.send_response("You don't have permission to do that")


@bot.slash_command(name="waitlist", description="Check your placement on the waitlist", ephemeral=True)
@commands.guild_only()
async def waitlist(ctx):
    session = Session()
    member = session.query(Member).filter(Member.discord_id == ctx.author.id).first()
    if member is None:
        await ctx.send_response("You are not in the database", ephemeral=True)
    else:
        members = (
            session.query(Member)
            .filter_by(is_vip=False, is_resumecv=False, is_invited=False)
            .order_by(Member.join_date, desc(Member.message_count))
            .all()
        )
        for i in members:
            print(i.discord_username)
        position = members.index(member) + 1
        await ctx.send_response(f"You are number {position} on the waitlist", ephemeral=True)
        logging.debug(f"{ctx.author.name} checked their position on the waitlist")
    session.close()


@bot.slash_command(name="invite", description="Set user as invited to bluesky")
async def invite(ctx, member: discord.Member, enable: bool):
    admin_found = False
    for role in ctx.author.roles:
        if role.id == ROLE:
            admin_found = True
            session = Session()
            member = session.query(Member).filter(Member.discord_id == member.id).first()
            member.is_invited = enable
            session.commit()
            if enable:
                await ctx.send_response(f"{member.discord_username} added to invited list")
            else:
                await ctx.send_response(f"{member.discord_username} removed from invited list")
            logging.debug(f"{ctx.author.name} added {member.discord_username} to invited list")
            session.close()
    if admin_found is False:
        await ctx.send_response("You don't have permission to do that")


@bot.event
async def on_member_join(member):
    session = Session()
    join_date = member.joined_at
    new_member = Member(
        discord_id=member.id,
        join_date=join_date,
        discord_username=member.name + member.discriminator,
        is_vip=False,
        is_resumecv=False,
        is_invited=False,
        message_count=0,
    )
    session.add(new_member)
    session.commit()
    session.close()
    logging.debug(f"{member.name} joined on {join_date} added to database")


@bot.event
async def on_member_remove(member):
    session = Session()
    member = session.query(Member).filter(Member.discord_id == member.id).first()
    session.delete(member)
    session.commit()
    session.close()
    logging.debug(f"{member.name} removed from database")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    session = Session()
    member = session.query(Member).filter(Member.discord_id == message.author.id).first()
    member.message_count += 1
    session.commit()
    session.close()


# run the bot
bot.run(os.getenv("DEV_TOKEN"))
