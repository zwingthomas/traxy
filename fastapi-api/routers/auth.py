from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas, deps

router = APIRouter(prefix='/api/auth')

@router.post('/signup', response_model=schemas.UserOut)
def signup(u: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    return crud.create_user(db, u)

@router.post('/login', response_model=schemas.Token)
def login(form_data: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user: raise HTTPException(401)
    token = crud.create_access_token({'sub': user.username})
    return {'access_token': token}