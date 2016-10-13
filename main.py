import webapp2
import os
import jinja2
import hash
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

class Handler(webapp2.RequestHandler):
    #writes to the current page
    def write(self, *a, **kw):
        self.response.write(*a, **kw)
    #takes an html file and saves renders it
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    #renders and html template that is passed in
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
    #get the current use cookie
    def get_user_cookie(self):
        return hash.check_hash(self.request.cookies.get('user', ''))
    #creates a cookie for a logged in user
    def login(self,username):
        self.response.headers.add_header('Set-Cookie', 'user=%s' % str(hash.hash_str(username)))
#an entity for blog posts
class BlogPosts(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    number = db.IntegerProperty(required=True)
    id = db.StringProperty(required=True)
    user = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    votes = db.IntegerProperty(required=True)
    voters = db.ListProperty(str)
#an entity for blog users
class users(db.Model):
    username = db.StringProperty(required=True)
    email = db.EmailProperty(required=True)
    password_hash = db.StringProperty(required=True)
    profile_picture = db.BlobProperty(required=False)
#an entity for comments
class comments(db.Model):
    username = db.StringProperty(required=True)
    post_id = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    id = db.StringProperty(required=True)

#handler for the main page
class MainPage(Handler):
    #passes blog posts and user name to be rendered
    def get(self):
        posts = db.GqlQuery("SELECT * FROM BlogPosts "
                            "ORDER BY created DESC ")
        user = self.get_user_cookie()
        blog_users = users.all()
        self.render("index.html",
                    posts = posts,
                    user = user)

    def post(self):
        #gets and saves user, blog post, and id of the blog posts
        user = self.get_user_cookie()
        if user == "":
            self.redirect("/login")
        else:
            posts = db.GqlQuery("SELECT * FROM BlogPosts")
            self.render("index.html", posts = posts)
            id = self.request.get("id")
            upvote = self.request.POST.get('upvote', None)
            downvote = self.request.POST.get('downvote', None)
            vote = 0
            has_voted = False
            if upvote:
                vote = 1
            else:
                vote = -1
            #cycles through blog posts and checks for an id match to add vote
            for post in posts:
                if str(post.id) == str(id):
                    for v in post.voters:
                        if str(v) == user:
                            has_voted = True
                    if has_voted == False:
                        post.votes += vote
                        post.voters.append(user)
                        post.put()
            self.redirect("/")

class Post_Blog(Handler):
    def generate_Blog_Id(self):
        is_unique = True
        #this generates a unique user id to be stored for every blog post
        #because the genratiopn is made up of 9 random upcase and lower case letters
        #this combinations is 52^9
        #there are 2,779,905,883,635,712 different unique id combinations
        id = hash.make_salt(9)
        posts = BlogPosts.all()
        for post in posts:
            if post.id == id:
                is_unique = False
        if is_unique == False:
            return str(self.generate_Blog_Id())
        else:
            return id
    def get(self):
        #redirects to login page if user is not logged in
        user = self.get_user_cookie()
        if user != "":
            self.render("post.html")
        else:
            self.redirect("/login")
    def post(self):
        user = self.get_user_cookie()
        if user != "":
            title = self.request.get("title")
            content = self.request.get("content")
            #checks if fields are filled in
            if title and content:
                blogposts = []
                posts = db.GqlQuery("SELECT * FROM BlogPosts")
                post_num = posts.count() + 1
                id = self.generate_Blog_Id()
                a = BlogPosts(title = title,
                              content = content,
                              number = post_num,
                              user=user,id=id,
                              votes=0)
                a.put()
                self.redirect('/posted?q='+id)
            else:
                title_error = ""
                content_error = ""
                if title == "":
                    title_error = "You're missing a title"
                if content == "":
                    content_error = " You're missing content"
                self.render("post.html",
                            content_error=content_error,
                            title_error=title_error,
                            title=title,
                            content=content )

class login(Handler):
    def get(self):
        self.render("login.html")
    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")
        user_exist = False
        pw_hash = ""
        users = db.GqlQuery("SELECT * FROM users")
        #checks if user exists
        for user in users:
            if username == user.username:
                user_exist = True
                break
        #form validation
        if username and password and user_exist == True:
            pw_hash = user.password_hash
            if hash.valid_pw_hash(username, password, pw_hash):
                self.login(username)
                self.redirect("/")
            else:
                self.render("login.html", username_error=" Wrong Username or Password")
        else:
            username_error = ""
            pass_error = ""
            if username == "":
                username_error = " please enter a username"
            if password == "":
                pass_error = " please enter a password"
            if user_exist == False:
                username_error = " Wrong Username or Password"
            self.render("login.html",
                        username_error=username_error,
                        password_error=pass_error)
class signup(Handler):
    def get(self):
        self.render("signup.html")
    def post(self):
        username_taken = False
        email_taken = False
        pass_match = True
        username = self.request.get("username")
        email = self.request.get("email")
        password = self.request.get("password")
        password_two = self.request.get("password_two")
        blog_users = db.GqlQuery("SELECT * FROM users")
        #checks for form validation and adds user to database
        for user in blog_users:
            if username == user.username:
                username_taken = True
            if email == user.email:
                email_taken = True
        if password != password_two:
            pass_match = False
        if username and email and password and password_two and \
                        username_taken == False and email_taken == False and pass_match == True:
            pass_hash = hash.make_pw_hash(username,password)
            a = users(username=username,
                      password_hash=pass_hash,
                      email=email)
            a.put()
            self.login(username)
            self.redirect("/")
        else:
            username_error = ""
            email_error = ""
            password_error = ""
            if username_taken == True:
                username_error = " This username is taken"
            if email_taken == True:
                email_error = " This email is already in use"
            if username == "":
                username_error = " Please enter a username"
            if email == "":
                email_error = " please enter a email"
            if password_two != password:
                password_error = " passwords do not match"
            if password_two == "":
                password_error = " please fill in both password fields"
            if password == "":
                password_error = " please enter a password"
            self.render("signup.html",
                        username_error=username_error,
                        email_error=email_error,
                        password_error=password_error)
class logout(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'user=""')
        self.redirect("/")

#handler for a single blog post
class posted_blog(Handler):
    #genrates an unique comment id
    def generate_comment_id(self):
        is_unique = True
        id = hash.make_salt(9)
        all_comments = comments.all()
        for comment in all_comments:
            if comment.id == id:
                is_unique = False
        if is_unique == False:
            return str(self.generate_comment_id())
        else:
            return id
    #gets comments and blog post to be rendered
    def get(self):
        user = self.get_user_cookie()
        id = self.request.get("q")
        posts = BlogPosts.all()
        all_comments = comments.all()
        post_comments = []
        for post in posts:
            if str(id) == str(post.id):
                cur_post = post
                break
        for comment in all_comments:
            if comment.post_id == str(id):
                post_comments.append(comment)
        self.render("singlepost.html",
                    post = cur_post,
                    comments = post_comments,
                    user = user)
    def post(self):
        user = self.get_user_cookie()
        post_id = self.request.get("q")
        delete_Button = self.request.POST.get('delete', None)
        submit_Button = self.request.POST.get('comment', None)
        comment_id = self.request.get("id")
        if user != "":
            if delete_Button:
                # gets comment by id and deletes it
                all_comments = comments.all()
                for c in all_comments:
                    #verifiest that the user owns this comment before deleting
                    if c.id == comment_id and c.username == user:
                        c.delete()
                self.redirect("/posted?q="+str(post_id))
            elif submit_Button:
                # checks for validation and adds comment
                id = self.generate_comment_id()
                content = self.request.get("commentContent")
                a = comments(username= user,post_id = str(post_id),content=content,id=id)
                a.put()
                self.redirect("/posted?q="+str(post_id))
        else:
            self.redirect("/login")
#handler for the user profile
class profile(Handler):
    def get(self):
        user = self.get_user_cookie()
        if user != "":
            posts = BlogPosts.all()
            profile_post = []
            for post in posts:
                if post.user == str(user):
                    profile_post.append(post)
            self.render("profile.html", posts = profile_post, user = user)
        else:
            self.redirect("/login")
    def post(self):
        #checks for user input for delete or edit
        cur_user = self.get_user_cookie()
        all_users = users.all()
        all_comments = comments.all()
        post_id= self.request.get("delete")
        edit_Button = self.request.POST.get('edit_item', None)
        delete_Button = self.request.POST.get('delete_item', None)
        if delete_Button:
            self.redirect("/")
            posts = BlogPosts.all()
            for post in posts:
                if post.id == str(post_id) and cur_user == post.user:
                    for comment in all_comments:
                        if comment.post_id == post_id:
                            comment.delete()
                    post.delete()
            self.redirect("/")
        elif edit_Button:
            self.redirect("/edit?B="+post_id)
        else:
            self.redirect("/login")

class account(Handler):
    #gets blog posts from a user id and renders the posts
    def get(self):
        cur_user = self.get_user_cookie()
        user = self.request.get("user")
        if user != cur_user:
            posts = BlogPosts.all()
            profile_post = []
            for post in posts:
                if post.user == str(user):
                    profile_post.append(post)
            self.render("account.html", posts=profile_post, user=user)
        else:
            self.redirect("/profile")
class edit(Handler):
    #passes blog id and fills title and content forms
    def get(self):
        user = self.get_user_cookie()
        post_id = self.request.get("B")
        posts = BlogPosts.all()
        editable = False
        title=""
        content=""
        for p in posts:
            if p.id == post_id and user == p.user:
                #checks to make sure the user is the owner of the blog post being edited
                #then sets editable to be true other wise redirects to the homepage
                title = p.title
                content = p.content
                editable = True
                break
        if editable == True:
            self.render("edit.html",
                        title=title,
                        content=content,
                        user=user)
        else:
            self.redirect("/")
    def post(self):
        #resumits blog post with changed content and title
        post_id = self.request.get("B")
        title = self.request.get("title")
        content = self.request.get("content")
        posts = BlogPosts.all()
        for p in posts:
            if p.id == post_id:
                p.title = title
                p.content = content
                p.put()
        self.redirect("/profile")
#redirects for the different webpages
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/post', Post_Blog),
    ('/posted', posted_blog),
    ('/login', login),
    ('/logout', logout),
    ('/signup', signup),
    ('/profile', profile),
    ('/account', account),
    ('/edit', edit)],
    debug=True)
