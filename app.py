from flask import Flask, redirect, render_template, request, flash, url_for, session
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import datetime
import requests
import os
#-------------------------------------------------------------------

app = Flask(__name__)

#-------------------------------------------------------------------
#Configuraciones para firebase
cred = credentials.Certificate("marmalade-account_private.json")
fire = firebase_admin.initialize_app(cred)
app.config["SECRET_KEY"] = "KOZLqCqDgYtxeRGarXnlnOQRamUiVArxSRbVhkYtIfEPmqipdH"
#Conexion a firestore DB = DataBase
db = firestore.client()
#Se crea la referencia de la base de datos
clientes_referencial = db.collection("Clientes")
ordenes_referencial = db.collection("Ordenes")
historial_referencial = db.collection("Historial")
users_referencial = db.collection("Users")
#Api web que se obtiene cuando se crea el proyecto en firebase
API_KEY = "AIzaSyBjy96v-OwqetmJTZe-BXNcCtKhQWnsBjM"
#Usuario para autentificarse por correo e email de manera administrativa para que pueda ingresar al Dashboard principal
user_authentication = False
#-------------------------------------------------------------------
#Login Administrativa 
#Solo se ingresara como Administración con un correo y contraseña registrado en Firebase
def login_firebas(email, password):
    credentials = {"email":email,"password":password,"returnSecureToken":True}
    response = requests.post("https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={}".format(API_KEY),data=credentials)
    if response.status_code == 200:
       dataa = response.json()
       user_login = (dataa["localId"])
       print(user_login)
       return user_login
    elif response.status_code == 400:
        print(response.content)    
    return False
#-------------------------------------------------------------------#-------------------------------------------------------------------
def get_ref_user(id):
    user_ref = users_referencial.document(id)
    user = user_ref.get()
    if user.exists:
        print(user.to_dict()) 
        docs_ref = user_ref.collection("Clientes")
    else:
        print("Cliente no encontrado")    
        docs_ref = False
    return docs_ref
#-------------------------------------------------------------------#-------------------------------------------------------------------
#leer varios documentos 
def leer_docs(referencial):
    docs = referencial.get()
    all_clients = []
    for doc in docs:
        list = doc.to_dict()
        list["id"] = doc.id
        all_clients.append(list)

    return all_clients   
#-------------------------------------------------------------------#-------------------------------------------------------------------
#Leer la información de un documento 
def leer_doc(referencial, id):
    documento = referencial.document(id).get()
    return documento.to_dict()
#-------------------------------------------------------------------#
## Funcion nueva para crear los clientes donde sole se llama referencial 
def leer_invidi(referencial):
    documentos = referencial.get()
    return documentos
#-------------------------------------------------------------------#-------------------------------------------------------------------
############ Creando las colecciones para el cliente, Ordenes y historial #############
#-------------------------------------------------------------------#-------------------------------------------------------------------
## Crear el clente por su nombre
def crear_cliente(referencial, name, date):
    information = {
        "name": name,
        "date": date,
    }
    referencial.document().set(information)
#-------------------------------------------------------------------#-------------------------------------------------------------------
## Crear la orden donde registre el nombre, cantidad, fecha
def crear_orden(referencial, name, cantid):
    cliente = buscar_client(name)
    if cliente != "No encontrado":
        information = {
            "name": name,
            "cantidad": cantid,
            "check": False,
            "fecha": datetime.datetime.now()
        }
        referencial.document().set(information)   
        crear_historial(historial_referencial, name, "Compra")
    else:
        print("El cliente no encontrado")
#-------------------------------------------------------------------#-------------------------------------------------------------------        
## Crear el historial de los clientes 
def crear_historial(referencial, name, action):
    if action == "Terminado":
        information = {
            "client": name,
            "action": action,
            "fecha": datetime.datetime.now()
        }
        referencial.document().set(information)
#--------------------------------------------------
    elif action == "Cancelado":
        information = {
            "cliente": name,
            "action": action,
            "fecha": datetime.datetime.now()
        }
        referencial.document().set(information) 
#--------------------------------------------------
    elif action == "Entregado":
        information = {
            "cliente": name,
            "action": action,
            "fecha": datetime.datetime.now()
        }
        referencial.document().set(information)    
#--------------------------------------------------
    elif action == "Compra":
        information = {
            "cliente": name,
            "action": action,
            "fecha": datetime.datetime.now()
        }
        referencial.document().set(information)  
        
#-------------------------------------------------------------------#-------------------------------------------------------------------
############Crear funciones para actualizar datos, eliminar datos, buscar datos y ordenes
def actualizar_doc(referencial, id):
    referencial.document(id).update({"check": True})    
#-------------------------------------------------------------------
def actualizar_orden(referencial, id):
    referencial.document(id).update({"check": True})
    doc = leer_doc(referencial, id)
    client = doc["name"]
    crear_historial(historial_referencial, client, "Terminado")
#-------------------------------------------------------------------#-------------------------------------------------------------------
def eliminar_doc(referencial, id):
    referencial.document(id).delete()
#-------------------------------------------------------------------#-------------------------------------------------------------------
## Eliminar la orden 
def eliminar_orden(referencial, id):
    doc = leer_doc(referencial, id)
    client = doc["name"]
    crear_historial(historial_referencial, client, "Cancelado")
    referencial.document(id).delete()
#-------------------------------------------------------------------
def service_delivery_orden(referencial, id):
    doc = leer_doc(referencial, id)
    client = doc["name"]
    crear_historial(historial_referencial, client, "Entregado")
    referencial.document(id).delete()
#-------------------------------------------------------------------#-------------------------------------------------------------------
## Buscar clientes registrado caso contrario mostrara un mensaje que el cliente no esta registrado o no encontrado
def buscar_client(name):
    print(f"Buscar clientes")
    clients = leer_invidi(clientes_referencial)
    #print(f"{clients}")
    ID_client = "No encontrado"
    for client in clients:
        c = client.to_dict() 
        c["id"] = client.id
        print(f"{c}")
        if c["name"] == name:
           ID_client = c["id"]
    return ID_client        
#-------------------------------------------------------------------#-------------------------------------------------------------------
########## Configuración de la pagina web
#-------------------------------------------------------------------#-------------------------------------------------------------------
########## Login de manera administrativa 
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "GET":
        if "user_login" in session:
            return redirect(url_for("home"))
        else:
            return render_template("login.html")

    elif request.method == "POST": #POST
      #Global
      global user_authentication

      email = request.form["email"]
      password = request.form["password"]
      print(f"{email}:{password}")
    try:
        user_login = login_firebas(email, password)
        print(f"Ingreso del usuario: {user_login}")
        user_authentication = get_ref_user(user_login)
        if user_login:
            session["user_login"] = user_login
            flash("Ingresaste correctamente!")
            return redirect(url_for("home"))
        else:
            print("Sesion fallida..")
            flash("Credenciales incorrectas")
            return redirect(url_for("login"))
    except:          
            print("Sesion fallida")
            flash("Credenciales incorrectas")
            return redirect (url_for("login"))  
#-------------------------------------------------------------------#-------------------------------------------------------------------
#Cierre de sesión
@app.route("/logout", methods=["GET", "POST"])
def login_left():
   if "user_login" in session:
      session.pop("user_login", None)
   return redirect(url_for("login"))
#-------------------------------------------------------------------#-------------------------------------------------------------------
@app.route("/", methods = ["GET"])
def home():
    if request.method == "GET":
        if user_authentication:
            try:
                orders = leer_docs(ordenes_referencial)
                clients = leer_docs(clientes_referencial)
                completed = []
                incompleted = []

                for order in orders:
                    if order["check"] == True:
                        completed.append(order)
                    else:
                        incompleted.append(order)

            except:
                orders = []
                print("Error...")                   
                print(len(incompleted))
            response = {"completed":completed, 
                        "incompleted":incompleted,
                        "completadas":len(completed),
                        "pendientes":len(incompleted),
                        "clientes":len(clients),
                        "all_clientes":clients}

            return render_template("index.html", response = response)
        else:
            return redirect(url_for("login"))
    else:
       #POST
        name = request.form["name"]
        date = request.form["date"]
        print(f"\n {name}")
        print(f"\n {date}")

        try:
            crear_cliente(clientes_referencial, name, date)
            return redirect("/")
        except:
            return render_template("error.html", response = "response")                
#-------------------------------------------------------------------#-------------------------------------------------------------------
@app.route("/ordenes", methods = ["GET", "POST"])
def ordenes():
    if request.method == "GET":
        try:
            ordens = leer_docs(ordenes_referencial)
            completed = []
            incompleted = []

            for orden in ordens:
                if orden["check"] == True:
                    completed.append(orden)
                else:
                    incompleted.append(orden)
        except:
            orden = []
            print("Error")
        response = {"completed":completed, 
                    "incompleted":incompleted,
                    "counter1":len(completed),
                    "counter2":len(incompleted)}
        return render_template("ordenes.html", response = response)
    else:
        name = request.form["name"]
        cantid = request.form["cantid"] 
        print(f"{name}, {cantid}")
     
        try:
            crear_orden(ordenes_referencial, name, cantid)
            return redirect("/ordenes")
        except:
            flash("Cliente no encontrado")
            return render_template("error.html", response = "response")                 
#-------------------------------------------------------------------#-------------------------------------------------------------------
@app.route("/clientes", methods = ["GET", "POST"])
def clientes():
    if request.method == "GET":
        try:
            clients = leer_docs(clientes_referencial)
        except:
            print("Error...")
        response = {"all_clientes": clients}
        return render_template("clientes.html", response = response)
    else:
        name = request.form["name"]
        print(f"{name}")
        date = request.form["date"]
        print(f"{date}")
        try:
            crear_cliente(clientes_referencial, name, date)
            return redirect("/clientes")
        except:
             return render_template("error.html", response = "response")                
#-------------------------------------------------------------------#------------------------------------------------------------------- 
@app.route("/historial", methods = ["GET"])
def historial():
    if request.method == "GET":
        try:
            history = leer_docs(historial_referencial)
           
        except:
            print("Error...")
        response = {"history": history}
        print(f"{history}")
        return render_template("historial.html", response = response)
    else:
        return render_template("error.html", response = "response")     

#-------------------------------------------------------------------#-----------------------------------------------------------------      
#Actualizar la orden
@app.route("/update/<string:id>", methods = ["GET"])
def update(id):
    print(f"\n Deseas actualizar la orden: {id}")
    try:
        actualizar_orden(ordenes_referencial, id)
        print("La orden fue actualizada...")
        return redirect("/")
    except:
         return render_template("error.html", response = "response")         
#-------------------------------------------------------------------#-------------------------------------------------------------------
## Eliminar la orden
@app.route("/delete/<string:id>", methods = ["GET"])
def delete(id):
    print(f"\n Deseas eliminar la orden {id}")
    try:
        eliminar_orden(ordenes_referencial, id)
        print("La orden fue eliminada...")
        return redirect("/")
    except:
      return render_template("error.html", response = "response")
#-------------------------------------------------------------------#-------------------------------------------------------------------
## Eliminar el cliente
@app.route("/deletec/<string:id>", methods = ["GET"])
def delete_client(id):
    print(f"\n Deseas eliminar el cliente {id}")    
    try:
        eliminar_doc(clientes_referencial, id)
        print("\n El cliente fue eliminado...")
        return redirect("/")
    except:
     return render_template("error.html", response = "response")
#-------------------------------------------------------------------#-------------------------------------------------------------------
## Eliminar el historial
@app.route("/deleteh/<string:id>", methods = ["GET"])
def delete_history(id):
    print(f"\n Deseas eliminar el historial {id}")   
    try:
        eliminar_doc(historial_referencial, id)
        print("El historial fue eliminado...")
        return redirect("/")
    except:
        return render_template("error.html", response = "response")    
#-------------------------------------------------------------------#-------------------------------------------------------------------
## Eliminar el historial de delivery
@app.route("/deletehd/<string:id>", methods = ["GET"])
def delete_delivery(id):
    print(f"\n Deseas eliminar el historial de delivery {id}")   
    try:
        service_delivery_orden(ordenes_referencial, id)
        print("El historial de delivery fue eliminado...")
        return redirect("/")
    except:
        return render_template("error.html", response = "response")    
#-------------------------------------------------------------------#-------------------------------------------------------------------                 
#----------------------------
#if __name__ == "__main__":
#    app.run(debug=True)
#---------------------------- 
#Para levantar el la aplicación web
PORT = int(os.environ.get("PORT",8080))
if __name__ == "__main__":
    app.run(threaded = True,host = "0.0.0.0", port = PORT)