drot - representing your models easy way 
========================================

Drot is small library that allows you to easy represent your model objects as a dictionaries and vice versa (DROT stands for REST data transfer objects).

Main intent was to simplify models representation as JSON in RESTful web services by removing typical models boilerplate code.

Suppose we writing some ordinary RESTful web service using ``flask`` with ``mongoengine`` and have three models (examples are from mongoengine documentation):

.. code-block:: python

    class BlogPost(Document):
        title = StringField(required=True, max_length=200)
        posted = DateTimeField(default=datetime.datetime.now)
        tags = ListField(StringField(max_length=50))


    class TextPost(BlogPost):
        content = StringField(required=True)


    class LinkPost(BlogPost):
        url = StringField(required=True)


Now we want to use this models in our RESTful web service:

.. code-block:: python

    @route('/posts')
    def list_posts():
        ...

    @route('/posts', method=['POST'])
    def make_post():
        ...


What code will be there instead of ``...``? 

Well, it depends:

.. code-block:: python

    post = BlogPost()
    post.title = request.json['title']
    post.posted = request.json['posted']
    post.tags = request.json['tags']


or :

.. code-block:: python

    post = BlogPost(**request.json) #  With all magic inside


or :

.. code-block:: python

    post = BlogPost.from_json(request.json) # With all eggs


In many and many other cases this code will be there. But do you really need to type this every time? I don't think so.

What ``drot`` does is very simple: it adds two methods to model (``to_dict`` and ``to_object``) based on a class definition.

By default, every model public attribute (that doesn't start with _) will be in output dictionary and will be accepted from input dictionary.
This will also work with ``@property`` decorator.

Rewrite our previous example using ``drot``:

.. code-block:: python

    import drot


    @drot.simple_model
    class BlogPost(Document):
        title = StringField(required=True, max_length=200)
        posted = DateTimeField(default=datetime.datetime.now)
        tags = ListField(StringField(max_length=50))

        
    @drot.simple_model
    class TextPost(BlogPost):
        content = StringField(required=True)

        
    @drot.simple_model
    class LinkPost(BlogPost):
        url = StringField(required=True)


    <somewhere else ...>

    @route('/posts')
    def list_posts():
        ...
        return jsonify({"values": [post.to_dict() for post in posts]})

    @route('/posts', method=['POST'])
    def make_post():
        post = BlogPost.to_object(request.json)


There are ``model`` decorator which helps you to parse nested objects:

.. code-block:: python
        
    @drot.simple_model
    class Author(Document):
        ...

    # you will get post.author = <Author object> after calling BlogPost.to_object 
    @drot.model(author=Author.to_object)
    class BlogPost(Document):
        author = None
        ...

``to_dict`` will recursively transform models to dictionaries and will fail if there is reference cycle.

There is ``excluded`` parameter for ``to_dict``:

.. code-block:: python

    @route('/posts')
    def posts():
        ...
        return jsonify({"values": [post.to_dict(excluded=['evil_value']) for post in posts]})


If you're desperate about what goes in and out from your models, you can specify whitelist of attributes that are allowed:

.. code-block:: python

    @drot.model('author', 'text', author=Author.to_object)
    class BlogPost(Document):
        author = None
        text = None
        evil_attribute = None #  Will never be in dictionary or passed from given dictionary
        ...


That's all it does.

There are only one requirement for models:

    1. It must be instantiable as Model()
