import concurrent.futures
import json


class JsonStore():

    def Ingest_to_Json(**kwargs):

        with open("./merge.json",'r+') as file:
            file_data = json.load(file)

            func = lambda x: file_data[kwargs["alias"]].append(x) #extracts generate item and appends to json
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                executor.map(func,kwargs['payload'])

            #Sets file's current position at offset.
            file.seek(0)
            # convert back to json.
            json.dump(file_data, file, indent = 4)


    def Log_to_Json():
        pass


