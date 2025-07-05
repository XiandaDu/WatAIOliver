from fastapi import Depends, FastAPI, Request, UploadFile, File, Form, Query, HTTPException, status

# old API used get_current_user to identify the user id in the db but we shouldn't need that anymore since we'll have WATIAM right?
def get_user_info():
    pass # call a users table in Supabase

def login():
    pass # need to implement uwaterloo SSO