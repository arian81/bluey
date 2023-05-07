import discord
from sqlalchemy import String, create_engine, Column, DateTime, Boolean, BigInteger, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase
import logging
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import os

MANAGER_ROLE_ID = 1103919524216062012
VIP_ROLE_ID = 1100501016090267756
BLUESKY_ROLE_ID = 1103599266187980900
UNVERIFIED_ROLE_ID = 1102277585628581959
load_dotenv()

logging.basicConfig(filename="logs.txt", level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


# SQLAlchemy database connection setup
engine = create_engine(os.getenv("PROD_DATABASE_URL"), echo=True)
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
    admin_found = False

    for role in ctx.author.roles:
        if role.id == MANAGER_ROLE_ID:
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
async def vip(ctx, discord_member: discord.Member, enable: bool):
    admin_found = False
    for role in ctx.author.roles:
        if role.id == MANAGER_ROLE_ID:
            admin_found = True
            session = Session()
            db_member = session.query(Member).filter(Member.discord_id == discord_member.id).first()
            db_member.is_vip = enable
            session.commit()
            if enable:
                await discord_member.add_roles(ctx.guild.get_role(VIP_ROLE_ID))
                await ctx.send_response(f"<@{db_member.discord_id}> added to VIP list")
            else:
                await discord_member.remove_roles(ctx.guild.get_role(VIP_ROLE_ID))
                await ctx.send_response(f"<@{db_member.discord_id}> removed from VIP list")
            logging.debug(f"{ctx.author.name} added <@{db_member.discord_id}> to VIP list")
            session.close()
    if admin_found is False:
        await ctx.send_response("You don't have permission to do that")


@bot.slash_command(name="resumecv", description="Add a member to the resume.cv list")
async def resumecv(ctx, discord_member: discord.Member, enable: bool):
    admin_found = False
    for role in ctx.author.roles:
        if role.id == MANAGER_ROLE_ID:
            admin_found = True
            session = Session()
            db_member = session.query(Member).filter(Member.discord_id == discord_member.id).first()
            db_member.is_resumecv = enable
            session.commit()
            if enable:
                await ctx.send_response(f"<@{db_member.discord_id}> added to resume.cv list")
            else:
                await ctx.send_response(f"<@{db_member.discord_id}> removed from resume.cv list")
            logging.debug(f"{ctx.author.name} added <@{db_member.discord_id}> to resume.cv list")
            session.close()
    if admin_found is False:
        await ctx.send_response("You don't have permission to do that")


@bot.slash_command(name="waitlist", description="Check your placement on the waitlist", ephemeral=True)
async def waitlist(ctx):
    for role in ctx.author.roles:
        if role.id == UNVERIFIED_ROLE_ID:
            await ctx.send_response("You are not verified", ephemeral=True)
            return
    session = Session()
    member = session.query(Member).filter(Member.discord_id == ctx.author.id).first()
    if member is None:
        await ctx.send_response("You are not in the database", ephemeral=True)
    elif member.is_invited:
        await ctx.send_response("You already have access to bluesky", ephemeral=True)
    else:
        members = (
            session.query(Member)
            .filter_by(is_invited=False)
            .order_by(desc(Member.is_vip), desc(Member.is_resumecv), Member.join_date, desc(Member.message_count))
            .all()
        )
        position = members.index(member) + 1
        await ctx.send_response(f"You are number {position} on the waitlist", ephemeral=True)
        logging.debug(f"{ctx.author.name} checked their position on the waitlist")
    session.close()


# only an admin should be able to run this command
@bot.slash_command(name="user_position", description="Check a member's position on the waitlist", ephemeral=True)
async def position(ctx, discord_member: discord.Member):
    admin_found = False
    for role in ctx.author.roles:
        if role.id == MANAGER_ROLE_ID:
            admin_found = True
            session = Session()
            db_member = session.query(Member).filter(Member.discord_id == discord_member.id).first()
            if db_member is None:
                await ctx.send_response("They are not in the database", ephemeral=True)
            elif db_member.is_invited:
                await ctx.send_response("They already have access to bluesky", ephemeral=True)
            else:
                members = (
                    session.query(Member)
                    .filter_by(is_invited=False)
                    .order_by(
                        desc(Member.is_vip), desc(Member.is_resumecv), Member.join_date, desc(Member.message_count)
                    )
                    .all()
                )
                position = members.index(db_member) + 1
                await ctx.send_response(
                    f"<@{db_member.discord_id}> is number {position} on the waitlist", ephemeral=True
                )
                logging.debug(f"{ctx.author.name} checked <@{db_member.discord_id}>'s position on the waitlist")
            session.close()
    if admin_found is False:
        await ctx.send_response("You don't have permission to do that", ephemeral=True)


# only an admin can run this command
@bot.slash_command(name="waitlist_position", description="Check user at a waitlist position", ephemeral=True)
async def waitlist_position(ctx, position: int):
    admin_found = False
    for role in ctx.author.roles:
        if role.id == MANAGER_ROLE_ID:
            admin_found = True
            session = Session()
            members = (
                session.query(Member)
                .filter_by(is_invited=False)
                .order_by(desc(Member.is_vip), desc(Member.is_resumecv), Member.join_date, desc(Member.message_count))
                .all()
            )
            if position > len(members):
                await ctx.send_response("There are not that many people on the waitlist", ephemeral=True)
            else:
                member = members[position - 1]
                await ctx.send_response(f"<@{member.discord_id}> is number {position} on the waitlist", ephemeral=True)
                logging.debug(f"{ctx.author.name} checked <@{member.discord_id}>'s position on the waitlist")
            session.close()
    if admin_found is False:
        await ctx.send_response("You don't have permission to do that", ephemeral=True)


@bot.slash_command(name="invite", description="Set user as invited to bluesky")
async def invite(ctx, discord_member: discord.Member, enable: bool):
    admin_found = False
    for role in ctx.author.roles:
        if role.id == MANAGER_ROLE_ID:
            admin_found = True
            session = Session()
            db_member = session.query(Member).filter(Member.discord_id == discord_member.id).first()
            db_member.is_invited = enable
            session.commit()
            if enable:
                await ctx.send_response(f"<@{db_member.discord_id}> added to invited list")
            else:
                await ctx.send_response(f"<@{db_member.discord_id}> removed from bluesky invited list")
            logging.debug(f"{ctx.author.name} added <@{db_member.discord_id}> to bluesky invited list")
            session.close()
    if admin_found is False:
        await ctx.send_response("You don't have permission to do that")


@bot.slash_command(name="syncroles", description="Syncs roles with database")
async def adminconfig(ctx):
    admin_found = False
    for role in ctx.author.roles:
        if role.id == MANAGER_ROLE_ID:
            admin_found = True

            session = Session()
            members = ctx.guild.members
            for member in members:
                for role in member.roles:
                    if role.id == VIP_ROLE_ID:
                        vip_member = session.query(Member).filter(Member.discord_id == member.id).first()
                        vip_member.is_vip = True
                        session.commit()
                    elif role.id == BLUESKY_ROLE_ID:
                        bluesky_member = session.query(Member).filter(Member.discord_id == member.id).first()
                        bluesky_member.is_invited = True
                        session.commit()
            session.close()
            await ctx.send_response("Sync is done")
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
bot.run(os.getenv("PROD_TOKEN"))
