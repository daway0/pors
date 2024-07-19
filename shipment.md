# Introduction

This code is developed and maintained outside the company's environment. To ensure the code is accessible to the company, please verify that the company has access to this repository by any means. To update the company code, the following steps must be performed in order.

# Step 1: Fetching Changes (git pull or git clone)

It doesn't matter if you `pull` the latest changes or `clone` the repository from scratch. The important thing is to check out the latest tag. Tags are usually ready for use in the production environment.

### Using `git pull`:
```sh
git pull origin main
git checkout <latest-tag>
```

# Step 2: Copying Files and Directories

1. The `pors` directory should be completely removed from the company's repository, and the new version should be replaced.
2. The `static/Pors` directory should also be fully replaced with the new version.
3. If there are any changes in `settings.py`, it should be completely replaced with the new version.


# Step 3: Apply Database Changes

Database changes should be applied using the following command:

```sh
python manage.py migrate pors
```
Note: There is no need to use `makemigrations` command since migration files have already been created in the development environment.

# Step 4: Update and Add Database Views

Database views that have changed need to be updated, and any new views should be added. You can find the database views in the `pors/SQLs` directory. Views with the prefix `v_` are database views. Note that the view name (the one to be registered in the database) follows the `v_` prefix.

Ensure that the database schema is aligned with the latest changes by executing the necessary SQL commands or scripts to reflect the updates and additions.


# Step 5: Configure Email Settings

The email settings need to be configured with the appropriate values provided in the text file in the company's repository. Update the settings as follows:

```python
# EMAIL_HOST = <value from text file>
EMAIL_HOST_USER = "pors@iraneit.com"
# BCC_EMAIL = <value from text file>
# EMAIL_HOST_PASSWORD = <value from text file>
# EMAIL_PORT = <value from text file>
# EMAIL_USE_TLS = True
```

Note that in this specific case, `BCC_EMAIL` should be set to the same value as `EMAIL_HOST_USER`.


# Step 6: Update Specific Locations

Locate and update the sections marked with `#todo shipment`. These are areas in the code that need to be modified according to the latest requirements or configurations related to shipment.

from 

```python
# todo shipment
# from Utility.Authentication.Utils import (
#     V1_PermissionControl as permission_control,
#     V1_get_data_from_token as get_token_data,
#     V1_find_token_from_request as find_token
# )

```

to
```python
# todo shipment
from Utility.Authentication.Utils import (
    V1_PermissionControl as permission_control,
    V1_get_data_from_token as get_token_data,
    V1_find_token_from_request as find_token
)

```


from 
```python
# todo shipment
# @permission_control
def auth_gateway(request):
    ...
```
to
```python
# todo shipment
@permission_control
def auth_gateway(request):
    ...
```

from 
```python
# todo shipment
    # token = find_token(request)
    # personnel = get_token_data(token, "username")
    # picture_name = get_token_data(token, "user_user_image_name")
    # email = get_token_data(token, "user_Email").lower()
    # full_name = get_token_data(token, "user_FullName")
    # is_admin = False
    # profile = profile_url(picture_name)

    personnel = "f.yousefi@eit"
    full_name = "erfan rezaee"
    profile = ""
    is_admin = False
    email = "e.rezaee@iraneit.com"
```
to
```python
# todo shipment
    token = find_token(request)
    personnel = get_token_data(token, "username")
    picture_name = get_token_data(token, "user_user_image_name")
    email = get_token_data(token, "user_Email").lower()
    full_name = get_token_data(token, "user_FullName")
    is_admin = False
    profile = profile_url(picture_name)

    # personnel = "f.yousefi@eit"
    # full_name = "erfan rezaee"
    # profile = ""
    # is_admin = False
    # email = "e.rezaee@iraneit.com"
```

from 
```python
# todo shipment
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

```
to
```python
# todo shipment
    # EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
```

# Step 7: Commit Changes and Perform Manual Testing

1. **Commit Changes**: Commit all the changes with a tag name matching the repository tag from outside the company.
2. **Deploy and Test:** After deploying the changes, perform manual testing to ensure that all features are working correctly. Verify that the updates are functioning as expected and that no issues have been introduced.





