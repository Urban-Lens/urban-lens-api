# How to Fix the Database Connection Issue

## Issue Summary

The Urban Lens API is currently experiencing a database connection error that prevents user registration and other operations. The specific error is:

```
AttributeError: 'AsyncSession' object has no attribute 'query'
```

This error occurs in the `get_by_email` method of the User model at:
```python
# models/users.py, line 55
return await db.query(cls).filter(cls.email == email).first()
```

## Root Cause

The API is using SQLAlchemy with AsyncSession, but the query syntax being used is for the synchronous version of SQLAlchemy. When using AsyncSession, the query API is different.

## Solution

The solution is to update the database query code to use the correct syntax for async SQLAlchemy. Here are the specific changes needed:

1. First, identify all methods in the API that use `db.query()` with AsyncSession.

2. Open the specific file (in this case `/models/users.py`) and locate the method with the issue:

```python
# Current code with error (models/users.py)
@classmethod
async def get_by_email(cls, db: AsyncSession, email: str):
    return await db.query(cls).filter(cls.email == email).first()
```

3. Replace with the correct async syntax:

```python
# Updated code for AsyncSession
@classmethod
async def get_by_email(cls, db: AsyncSession, email: str):
    query = select(cls).where(cls.email == email)
    result = await db.execute(query)
    return result.scalars().first()
```

4. Make sure to import the necessary SQLAlchemy functions:

```python
from sqlalchemy import select
```

5. Check all other database query methods in the API and apply similar changes where needed.

## Additional Changes

Make sure all the database operations follow the same pattern. Here's how different operations should be updated:

### SELECT queries

```python
# From:
result = db.query(Model).filter(Model.column == value).all()

# To:
query = select(Model).where(Model.column == value)
result = await db.execute(query)
records = result.scalars().all()
```

### INSERT operations

```python
# From:
db_item = Model(**data)
db.add(db_item)
await db.commit()
await db.refresh(db_item)

# To (largely the same):
db_item = Model(**data)
db.add(db_item)
await db.commit()
await db.refresh(db_item)
```

### UPDATE operations

```python
# From:
db_item = db.query(Model).filter(Model.id == item_id).first()
for key, value in data.items():
    setattr(db_item, key, value)
await db.commit()

# To:
query = select(Model).where(Model.id == item_id)
result = await db.execute(query)
db_item = result.scalars().first()
for key, value in data.items():
    setattr(db_item, key, value)
await db.commit()
```

### DELETE operations

```python
# From:
db_item = db.query(Model).filter(Model.id == item_id).first()
await db.delete(db_item)
await db.commit()

# To:
query = select(Model).where(Model.id == item_id)
result = await db.execute(query)
db_item = result.scalars().first()
await db.delete(db_item)
await db.commit()
```

## Testing the Fix

After making these changes, the user registration functionality should work correctly. You can test it using the `tests/test_registration.py` script: 