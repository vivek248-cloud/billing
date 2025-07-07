from django.shortcuts import redirect
import functools

def session_login_required(view_func):
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if the user is logged in by checking session variables
        if request.session.get('admin_logged_in') or request.session.get('user_logged_in'):
            return view_func(request, *args, **kwargs)
        return redirect('/home/')  # Redirect to home page if not logged in
    return wrapper