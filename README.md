# comparison-backend

Right now the dockerfile starts flask backend on port 5000, however requests are not processed correctly. 

To create and run docker container:

docker build -t backend .

docker run -d -p 5000:5000 backend

################################

just run python api.py for now
