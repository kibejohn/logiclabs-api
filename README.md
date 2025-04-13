# logiclabs-api
API for scorecards, decsion matrixes and workflow automation


brew services start postgresql

python3 -m venv venv   
source venv/bin/activate

python3 -m pip install 

python3 -m pip install -r requirements.txt

Check the Database Connection
psql -U kibejohn -d scorecard_db -h localhost

python -m uvicorn app.main:app --reload

alembic revision --autogenerate -m "Added percentage_threshold to scorecard"

alembic upgrade head

deploy

## deploy on azure

az webapp deployment source show --name logiclabs-api --resource-group cladfylandingpages_group

az webapp deployment source config-local-git --name logiclabs-api --resource-group cladfylandingpages_group

az webapp deployment source config --name logiclabs-api --resource-group cladfylandingpages_group --branch main --git-url https://johnkibemwangi2016%40gmail.com@logiclabs-api-acfrcyg0b0dnabcg.scm.westus-01.azurewebsites.net/logiclabs-api.git

git remote add azure "URL"

git push azure main
git push azure main:master

az webapp restart --name logiclabs-api --resource-group cladfylandingpages_group

## Delete github workflows

gh run list --limit 100 --status completed --json databaseId | jq '.[].databaseId' | xargs -n 1 gh run delete

gh run list --limit 100 --status completed | tail -n +2 | awk '{print $1}' | xargs -n 1 gh run delete