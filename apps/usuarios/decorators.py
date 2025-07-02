from django.contrib.auth.decorators import user_passes_test

def manager_required(function=None, redirect_field_name='next', login_url='login'):
    """
    Decorator for views that checks that the user is a manager, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_manager,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator