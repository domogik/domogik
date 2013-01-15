from domogik.xpl.lib.rest.url import urlHandler

@urlHandler.route('/blah')
def hello_world2():
  return 'This comes from blah ^_^'
