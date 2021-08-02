from email import encoders
from email.mime import base
from email.mime import image
from email.mime import multipart
from email.mime import text

import aiosmtplib

import config

mail_params = {
    "SSL": True,
    "host": "smtp.gmail.com",
    "password": config.HOST_EMIL_PASSWORD,
    "user": config.HOST_EMAIL,
    "port": 465,
}


def setup_email_contents(
    to: list, subject: str, contents: dict, sender: str = config.HOST_EMAIL,
) -> multipart.MIMEMultipart:
    """Setup an outgoing email with the given parameters and attachments.
    :param sender: From whom the email is being sent
    :type sender: str
    :param to: A list of recipient email addresses.
    :type to: list
    :param subject: The subject of the email.
    :type subject: str
    :param contents: Dictionary with email contents.
    :type contents: dict
    :returns
    """

    msg = multipart.MIMEMultipart()
    msg.preamble = subject
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(to)

    if "text" in contents.keys():
        content = contents["text"]
        msg.attach(text.MIMEText(content, _charset="utf-8"))
    if "html" in contents.keys():
        content, content_type = contents["html"]
        msg.attach(text.MIMEText(content, content_type, "utf-8"))
    if "image" in contents.keys():
        img, img_cid = contents["image"]
        email_image = image.MIMEImage(img)
        email_image.add_header("Content-ID", f"<{img_cid}>")
        msg.attach(email_image)
    if "attachments" in contents.keys():
        for attachment in contents["attachments"]:
            attachment_data, name = attachment
            attach = base.MIMEBase("application", "octet-stream")
            attach.set_payload(attachment_data)
            encoders.encode_base64(attach)
            attach.add_header("Content-Disposition", "attachment", filename=name)
            msg.attach(attach)

    return msg


class EmailAPI(object):

    __slots__ = ["__smtp"]

    def __init__(self):
        host = mail_params.get("host", "localhost")
        is_ssl = mail_params.get("SSL", False)
        port = mail_params.get("port", 465 if is_ssl else 25)

        self.__smtp = aiosmtplib.SMTP(hostname=host, port=port, use_tls=is_ssl)

    async def send_email(self, msg: multipart.MIMEMultipart):
        return await self.__smtp.send_message(msg)

    async def __aenter__(self):
        await self.__smtp.connect()
        await self.__smtp.login(mail_params["user"], mail_params["password"])
        return self.send_email

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.__smtp.quit()
        except Exception as e:
            print(f"SMTP server quit fail: {e}")


