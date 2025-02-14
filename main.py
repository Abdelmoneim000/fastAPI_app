# python build-in modules
import sys
import cmd
import os

# 3rd party modules
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# deploy modules
from asgiref.wsgi import WsgiToAsgi

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./shop.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Product Model (Database)
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Integer)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Model (API Request/Response)
class ProductCreate(BaseModel):
    name: str
    description: str
    price: int

# FastAPI App Instance
app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/")
def read_root():
    return {"message": "Welcome to our shop!"}

@app.post("/products/", response_model=ProductCreate)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/")
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}

# CLI using cmd module
class ShopCLI(cmd.Cmd):
    intro = "Welcome to the Shop CLI! Type 'help' or '?' to list commands.\n"
    prompt = "(shop) "
    
    def do_list(self, arg):
        """List all products"""
        db = SessionLocal()
        products = db.query(Product).all()
        db.close()
        if products:
            for product in products:
                print(f"{product.id}. {product.name} - {product.description} (${product.price})")
        else:
            print("No products found.")

    def do_add(self, arg):
        """Add a new product: add <name> <description> <price>"""
        args = arg.split(" ", 2)
        if len(args) < 3:
            print("Usage: add <name> <description> <price>")
            return
        name, description, price = args[0], args[1], args[2]
        try:
            price = int(price)
            db = SessionLocal()
            new_product = Product(name=name, description=description, price=price)
            db.add(new_product)
            db.commit()
            db.refresh(new_product)
            db.close()
            print(f"Product '{new_product.name}' added successfully!")
        except ValueError:
            print("Error: Price must be a number.")

    def do_delete(self, arg):
        """Delete a product by ID: delete <id>"""
        try:
            product_id = int(arg)
            db = SessionLocal()
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                print("Error: Product not found")
            else:
                db.delete(product)
                db.commit()
                print(f"Product '{product.name}' deleted successfully!")
            db.close()
        except ValueError:
            print("Error: ID must be a number.")

    def do_exit(self, arg):
        """Exit the CLI"""
        print("Goodbye!")
        return True

# Entry Point
if __name__ == "__main__":
    if os.getenv("VERCEL"):
        import uvicorn
        handler = WsgiToAsgi(app)

    elif len(sys.argv) > 1 and sys.argv[1] == "cli":
        ShopCLI().cmdloop()

    else:
        print("Starting FastAPI server...")
        import uvicorn
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
