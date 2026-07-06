"""Script contenente i parametri di mapping verso il dispatcher LayerAI"""
from string import Template

DISPATCHER_URL_TEST = Template("https://ai4y0-test.cloudapps-test.intesasanpaolo.com/api/v${version}/")
DISPATCHER_URL_PROD = Template("https://ai4y0-prod.cloudapps.intesasanpaolo.com/api/v${version}/")

dispatcher_gateway_url = {"svis": DISPATCHER_URL_TEST, "ptes": DISPATCHER_URL_TEST, "prod": DISPATCHER_URL_PROD}