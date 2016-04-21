# introduction

apiuser is an uliweb app which add support to easy interface to non-browser tools for using uliweb auth.

# api example
http get for example,but not recommended, but **http post** is more **recommended**, because http get have to escape for some charactor and will log password or token in accesslog
for token, you can also placing it in cookies(like browser)

```
$ curl http://localhost:8000/apiuser/api_get_auth
{"username":null}
$ curl "http://localhost:8000/apiuser/api_login?username=example_user&password=example_pass"
{"msg":"log in successfully","token_name":"apiuser_token","timeout":3600,"token":"153222cd9a7c66e3e39a6da607b6cba4","success":true}
$ curl http://localhost:8000/apiuser/api_get_auth?apiuser_token=153222cd9a7c66e3e39a6da607b6cba4
{"username":"example_user"}
$ curl http://localhost:8000/apiuser/api_logout?apiuser_token=153222cd9a7c66e3e39a6da607b6cba4a607b6cba4
{"msg":"user logout successfully","success":true}
```

# settings
**settings.AUTH_APIUSER.LOGIN_AUTH_TYPE_RESTRICTED** is a switch for whether the api can be used for all the auth type or just for **settings.AUTH.AUTH_TYPE_APIUSER** type user
