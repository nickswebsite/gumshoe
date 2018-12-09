
jsTarget = "gumshoe/static/js"

coffeeSrc = "webapp/coffee"

nodeModulesDir = "node_modules"

dependencySources = [
  "angular/angular.js"
  "angular-ui-bootstrap/ui-bootstrap.js"
  "urijs/src/URI.js"
]

childProcess = require 'child_process'
exec = childProcess.exec


task "coffee", "Compile CoffeeScript", ->
  exec "coffee -c -o #{jsTarget}/ #{coffeeSrc}/*.coffee"

task "dependencies", "Copy dependencies", ->
  for dependency in dependencySources
    exec "cp #{nodeModulesDir}/#{dependency} #{jsTarget}"


task "build", "Build webapp", ->
  invoke "coffee"
  invoke "dependencies"
