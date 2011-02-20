from apps.core.django_auth import login
from libs.decorators import render_to

@render_to("index.haml")
def index(request):
    return {}