An API key is created in the Demo data (for development), using the Demo
user. The key to use in the HTTP header `API-KEY` is: 72B044F7AC780DAC

Curl example:

    curl -X POST "http://localhost:8069/shopfloor/user/menu" -H  "accept: */*" -H  "Content-Type: application/json" -H "API-KEY: 72B044F7AC780DAC"

## Routes

Each app stores only one route (its `api_route`) in the `endpoint_route` table.
The routes of the services are generated when the routing map is built
(see the generators of `endpoint_route_handler`):
`/shopfloor/api/<app tech name>/<service usage>/<endpoint>`.

New services and endpoints are routed as soon as the code is loaded
(restart or module install/update): no install hook nor migration is needed
to register them. Same for removed ones.

To customize the routes of an app, extend `shopfloor.app._generate_routes`
or `_generate_service_routes`.
