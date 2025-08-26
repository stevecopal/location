from django.contrib.sessions.models import Session

def login_user(request, user, user_type):
    request.session['user_id'] = str(user.id)
    request.session['user_type'] = user_type
    request.session.modified = True

def logout_user(request):
    request.session.flush()