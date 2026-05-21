from flask import render_template, request
class AuthController:
    def home(self):
        return render_template("home.html")

    def login(self):
        if request.method=="POST":
            print(request.form)
        return render_template("login.html")
    
    def register(self):
        return render_template("register.html")
    
    def about(self):
        return render_template("about.html")
    
    def contact(self):
        return render_template("contact.html")