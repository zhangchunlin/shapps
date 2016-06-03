# introduction

lenovo id user is an uliweb app which add support to use lenovo id auth.
More info:http://open.lenovo.com/sdk/category/lenovo-id/

# api example
http get for example,but not recommended, but **http post** is more **recommended**, because http get have to escape for some charactor and will log password or token in accesslog
for token, you can also placing it in cookies(like browser)

```
$ curl http://localhost:8000/lenovoid/api_get_auth
{"username":null}
$ curl "http://localhost:8000/lenovoid/api_login?lpsust=zcvasdfasdfasdfasd
{"timeout":3600,"unlock_token":"153222cd9a7c66e3e39a6da607b6cba4"}
$ curl http://localhost:8000/lenovoid/api_get_auth?unlock_token=153222cd9a7c66e3e39a6da607b6cba4
{"username":"example_user"}
$ curl http://localhost:8000/lenovoid/api_logout?unlock_token=153222cd9a7c66e3e39a6da607b6cba4a607b6cba4
{"msg":"user logout successfully","success":true}
```