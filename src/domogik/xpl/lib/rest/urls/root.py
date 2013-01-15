from domogik.xpl.lib.rest.url import urlHandler

@urlHandler.route('/')
def hello_world():
  return 'This comes from Flask ^_^'

