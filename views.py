from flask import Flask, render_template, request, redirect, url_for, flash, \
    jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Users, Categories, Items

from flask import session as login_session
import random
import string
import os

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Sign in page
# Create a state token to prevent request forgery
# Store it in the session for later validation.
# Create anti-forgery state token
@app.route('/login/')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in list(range(32)))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    console.log("The current session state is %s" % login_session['state'])
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        console.log(response)
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        login_session['access_token'] = credentials.access_token
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    print (data)

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if user exists; and if not, make a new one.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; \
        border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


# DISCONNECT - Revoke a current user's token and reset their login_session.
@app.route("/gdisconnect/")
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        print ('Access token is none')
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    # Execute HTTP GET request to revoke current token.
    # access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print ('result is ')
    print (result)
    if result['status'] == '200':
        # Reset the user's session.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # Token was invalid
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON API Endpoint (GET)
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Categories).all()
    return jsonify(Catgegories=[c.serialize for c in categories])


@app.route('/catalog/<category>/JSON')
def categoryJSON(category):
    search = session.query(Categories).filter_by(name=category).first()
    items = session.query(Items).filter_by(category_type=search.name).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<category>/<item>/JSON')
def itemJSON(category, item):
    search = session.query(Categories).filter_by(name=category).first()
    thisItem = session.query(Items).filter_by(
        category_type=search.name).first()
    return jsonify(Items=thisItem.serialize)


# CATALOG FUNCTIONALITY


# Show all catalog and latest items
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Categories).all()
    return render_template('catalog.html', categories=categories)


# Create new category ONLY IF LOGGED IN
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        duplicate = session.query(Categories).filter_by(
            name=request.form['name']).first()
        if not duplicate:
            newCategory = Categories(name=request.form['name'])
            newCategory.user_id = login_session['user_id']
            session.add(newCategory)
            session.commit()
            flash("New category created!")
            return redirect('/catalog/')
        else:
            flash("Category creation unsuccessful. Already exists.")
            return redirect('/catalog/')
    else:
        return render_template('newCategory.html')


# Edit an existing category ONLY IF LOGGED IN (AND OWNER)
@app.route('/catalog/edit/', methods=['GET', 'POST'])
def editCategory():
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Categories).filter_by(
                                user_id=login_session['user_id'])
    if request.method == 'POST':
        search = session.query(Categories).filter_by(
            name=request.form['selectedCategory']).first()
        old = session.query(Items).filter_by(category_type=search.name).all()
        search.name = request.form['newName']
        for o in old:
            o.category_type = request.form['newName']
            session.add(o)
        session.add(search)
        session.commit()
        flash("Category successfully edited!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html', categories=categories)


# Delete category ONLY IF LOGGED IN (AND OWNER)
@app.route('/catalog/delete/', methods=['GET', 'POST'])
def deleteCategory():
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Categories).filter_by(
        user_id=login_session['user_id']).all()
    if request.method == 'POST':
        search = request.form['pickCategory']
        deleteCategory = session.query(Categories).filter_by(
            name=search).first()
        session.delete(deleteCategory)
        session.commit()
        flash("Category successfully deleted!")
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html', categories=categories)


# Show items in category
@app.route('/catalog/<category>/')
def showCategory(category):
    showCategory = session.query(Categories).filter_by(
                                name=category).one()
    creator = getUserInfo(showCategory.user_id)
    items = session.query(Items).filter_by(category_type=showCategory.name)
    if 'username' not in login_session:
        return render_template('publicCategory.html', category=showCategory)
    return render_template('category.html', category=showCategory, items=items)


# Show item and description along with edit/delete links
@app.route('/catalog/<category>/<item>/')
def showItem(category, item):
    thisItem = session.query(Items).filter_by(name=item).first()
    owner = getUserInfo(thisItem.user_id)
    category = session.query(Categories).filter_by(name=category).first()
    if 'username' not in login_session or owner.id != login_session['user_id']:
        return render_template('publicItem.html', item=thisItem)
    else:
        return render_template('item.html', item=thisItem)


# Create new item in category ONLY IF LOGGED IN
@app.route('/items/new/', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    allCategories = session.query(Categories).all()
    if request.method == 'POST':
        createdItem = Items(name=request.form['name'],
                            description=request.form['description'],
                            category_type=request.form['category'],
                            user_id=login_session['user_id'])
        session.add(createdItem)
        session.commit()
        flash("New item created!")
        return redirect(url_for('showCategory',
                                category=createdItem.category_type))
    else:
        return render_template('newItem.html', categories=allCategories)


# Edit existing item ONLY IF LOGGED IN (AND OWNER--of item)
@app.route('/catalog/<category>/<item>/edit/', methods=['GET', 'POST'])
def editItem(category, item):
    if 'username' not in login_session:
        return redirect('/login')
    thisItem = session.query(Items).filter_by(name=item).first()
    owner = getUserInfo(thisItem.user_id)
    if owner.id != login_session['user_id']:
        flash("You are not authorized to edit this item. \
            Create your own first!")
        return redirect(url_for('showCategory', category=category))
    editedItem = session.query(Items).filter_by(
        name=thisItem.name).first()
    categories = session.query(Categories).all()
    if request.method == 'POST':
        if request.form['category'] and request.form['name'] \
                                    and request.form['description']:
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            editedItem.category_type = request.form['category']
            session.add(editedItem)
            session.commit()
            flash("Item successfully edited!")
            return redirect(url_for('showItem',
                            category=editedItem.category_type,
                            item=editedItem.name))
        elif request.form['category'] and request.form['name']:
            editedItem.name = request.form['name']
            editedItem.category_type = request.form['category']
            session.add(editedItem)
            session.commit()
            flash("Item successfully edited!")
            return redirect(url_for('showItem',
                            category=editedItem.category_type,
                            item=editedItem.name))
        elif request.form['category'] and request.form['description']:
            editedItem.category_type = request.form['category']
            editedItem.description = request.form['description']
            session.add(editedItem)
            session.commit()
            flash("Item successfully edited!")
            return redirect(url_for('showItem',
                                    category=editedItem.category_type,
                                    item=editedItem.name))
        elif request.form['name'] and request.form['description']:
            editedItem.name = request.form['name']
            editedItem.description = request.form['description']
            session.add(editedItem)
            session.commit()
            flash("Item successfully edited!")
            return redirect(url_for('showItem',
                            category=editedItem.category_type,
                            item=editedItem.name))
        elif request.form['category'] and not request.form['name'] \
                and not request.form['description']:
            editedItem.category_type = request.form['category']
            session.add(editedItem)
            session.commit()
            flash("Item successfully edited!")
            return redirect(url_for('showItem',
                                    category=editedItem.category,
                                    item=editedItem.name))
        elif request.form['name'] and not request.form['category'] \
                and not request.form['description']:
            editedItem.name = request.form['name']
            session.add(editedItem)
            session.commit()
            flash("Item successfully edited!")
            return redirect(url_for('showItem',
                            category=editedItem.category_type,
                            item=editedItem.name))
        elif request.form['description'] and not request.form['name'] \
                and not request.form['category']:
            editedItem.description = request.form['description']
            session.add(editedItem)
            session.commit()
            flash("Item successfully edited!")
            return redirect(url_for('showItem',
                            category=editedItem.category_type,
                            item=editedItem.name))
        else:
            return redirect(url_for('emptyForm'))
    else:
        return render_template(
                                'editItem.html', category=category,
                                item=editedItem, categories=categories)


@app.route('/emptyform')
def emptyForm():
    return "You tried to submit an empty form!"


# Delete existing item ONLY IF LOGGED IN (AND OWNER--of item)
@app.route('/catalog/<category>/<item>/delete/', methods=['GET', 'POST'])
def deleteItem(category, item):
    deleteItem = session.query(Items).filter_by(name=item).first()
    owner = getUserInfo(deleteItem.user_id)
    if 'username' not in login_session:
        return redirect('/login')
    deleteItem = session.query(Items).filter_by(name=item).first()
    if owner.id != login_session['user_id']:
        flash("You are not authorized to edit this item. \
            Create your own first!")
        return redirect(url_for('showCategory', category=category))
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash("Item successfully deleted!")
        return redirect(url_for('showCategory', category=category))
    else:
        return render_template(
                                'deleteItem.html',
                                item=deleteItem, category=category)


def getUserInfo(user_id):
    user = session.query(Users).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(Users).filter_by(email=email).one()
        return user.id
    except:
        return None


def createUser(login_session):
    newUser = Users(username=login_session['username'],
                    email=login_session['email'],
                    picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(Users).filter_by(
        username=login_session['username']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
