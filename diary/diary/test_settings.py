from .settings import *


def gen_html():
    return "This is a **Martor** field."


MOMMY_CUSTOM_FIELDS_GEN = {
    'martor.models.MartorField': gen_html,
}
