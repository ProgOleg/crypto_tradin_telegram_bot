import datetime

from sqlalchemy.ext import declarative
import sqlalchemy as sa

Base = declarative.declarative_base()
metadata = Base.metadata


class User(Base):
    __tablename__ = "user"

    chat_id = sa.Column("chat_id", sa.BigInteger, primary_key=True)
    registration_date = sa.Column("registration_date", sa.DateTime, default=datetime.datetime.utcnow)
    language = sa.Column("language", sa.String(255))
    username = sa.Column("username", sa.String(255))
    # ban


class Order(Base):
    __tablename__ = "order"

    id = sa.Column("id", sa.BigInteger, sa.Identity(start=1000, increment=1), primary_key=True)
    user_id = sa.Column("user_id", sa.ForeignKey("user.chat_id"))
    quantity = sa.Column("quantity", sa.DECIMAL, nullable=False)
    exchange_type = sa.Column("exchange_type", sa.String(255), nullable=False)
    crypto = sa.Column("crypto", sa.String(255), nullable=False)
    fiat = sa.Column("fiat", sa.String(255), nullable=False)
    memo = sa.Column("memo", sa.String(255), nullable=True)
    # rename total_cost
    cost_fiat = sa.Column("cost_fiat", sa.DECIMAL, nullable=True)
    payment_type = sa.Column("payment_type", sa.String(255))
    bill = sa.Column("bill", sa.String(1024))

    cr_date = sa.Column("cr_date", sa.DateTime, default=datetime.datetime.utcnow)
    success = sa.Column("success", sa.Boolean, default=False)
    success_date = sa.Column("success_date", sa.DateTime)
    approve = sa.Column("approve", sa.Boolean)
    approved_date = sa.Column("approved_date", sa.DateTime)


class Admins(Base):
    __tablename__ = "admins"

    chat_id = sa.Column("chat_id", sa.BigInteger, primary_key=True)
    email = sa.Column("email", sa.String(255))
    is_active = sa.Column("is_active", sa.Boolean, default=True)


class Settings(Base):
    __tablename__ = "settings"

    markup = sa.Column("markup", sa.DECIMAL, primary_key=True)


class EWallets(Base):
    __tablename__ = "e_wallets"

    identifier = sa.Column("identifier", sa.String(10), nullable=False, unique=True, primary_key=True)
    wallet = sa.Column("wallet", sa.String(1024), nullable=False)
    memo = sa.Column("memo", sa.String(1024), nullable=True)
    description = sa.Column("description", sa.String(255), nullable=True)
