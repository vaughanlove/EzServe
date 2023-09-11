from src import autoserve 

server = autoserve.AutoServe()
test = server.agent.run("Could I order a small coffee please?")
print(test)
# need to mess with concurrency?
# here is where the chirp model records/transcribes/returns string


    