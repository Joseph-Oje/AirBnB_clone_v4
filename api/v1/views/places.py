#!/usr/bin/python3
"""
Flask route that returns json status response
"""
from api.v1.views import app_views
from flask import abort, jsonify, request
from flasgger.utils import swag_from
from models import storage, CNC
from os import environ
STORAGE_TYPE = environ.get('HBNB_TYPE_STORAGE')


@swag_from('swagger_yaml/places_by_city.yml', methods=['GET', 'POST'])
@app_views.route('/cities/<city_id>/places', methods=['GET', 'POST'])
def places_per_city(city_id=None):
    """
        places route to handle http method for requested places by city
    """
    city_obj = storage.get('City', city_id)
    if city_obj is None:
        abort(404, 'Not found')

    if request.method == 'GET':
        all_places = storage.all('Place')
        city_places = [obj.to_json() for obj in all_places.values()
                       if obj.city_id == city_id]
        return jsonify(city_places)

    if request.method == 'POST':
        req_json = request.get_json()
        if req_json is None:
            abort(400, 'Not a JSON')
        user_id = req_json.get("user_id")
        if user_id is None:
            abort(400, 'Missing user_id')
        user_obj = storage.get('User', user_id)
        if user_obj is None:
            abort(404, 'Not found')
        if req_json.get("name") is None:
            abort(400, 'Missing name')
        Place = CNC.get("Place")
        req_json['city_id'] = city_id
        new_object = Place(**req_json)
        new_object.save()
        return jsonify(new_object.to_json()), 201


@swag_from('swagger_yaml/places_id.yml', methods=['GET', 'DELETE', 'PUT'])
@app_views.route('/places/<place_id>', methods=['GET', 'DELETE', 'PUT'])
def places_with_id(place_id=None):
    """
        places route to handle http methods for given place
    """
    place_obj = storage.get('Place', place_id)
    if place_obj is None:
        abort(404, 'Not found')

    if request.method == 'GET':
        return jsonify(place_obj.to_json())

    if request.method == 'DELETE':
        place_obj.delete()
        del place_obj
        return jsonify({}), 200

    if request.method == 'PUT':
        req_json = request.get_json()
        if req_json is None:
            abort(400, 'Not a JSON')
        place_obj.bm_update(req_json)
        return jsonify(place_obj.to_json()), 200


@app_views.route('/places_search', methods=['POST'])
def places_search():
    """
        places route to handle http method for request to search places
    - if no json, return all places
    - check if states was provided & valid, if so, find all cities per state
    - check if cities provided & valid, if so, add extra cities to previous
      - state cities if there were any
    - checks if amenities was provide & valid id
    - if no amenities and no cities, return all places
    - generate valid places based off of provided cities
    - return all places for given cities if no amenities
    - generate valid places from given amenities and cities
    - verifies that all provided amenities are in the place amenities
    """
    all_places = storage.all('Place')

    req_json = request.get_json()
    if req_json is None:
        return jsonify([
            place.to_json() for place in all_places.values()
        ])
    states = req_json.get('states')
    if states and len(states) > 0:
        all_cities = storage.all('City')
        state_cities = set([
            city.id for city in all_cities.values()
            if city.state_id in states
        ])
    else:
        state_cities = set()
    cities = req_json.get('cities')
    if cities and len(cities) > 0:
        cities = set([
            c_id for c_id in cities if storage.get('City', c_id)
        ])
        state_cities = state_cities.union(cities)
    amenities = req_json.get('amenities')
    if (amenities is None or len(amenities) == 0) and len(state_cities) == 0:
        return jsonify([
            place.to_json() for place in all_places.values()
        ])
    if amenities and len(amenities) > 0:
        amenities = set([
            a_id for a_id in amenities if storage.get('Amenity', a_id)
        ])
    places = [
        p for p in all_places.values() if p.city_id in state_cities
    ]
    if amenities is None or len(amenities) == 0:
        return jsonify([p.to_json() for p in places])
    places_amenities = []
    for p in places:
        if STORAGE_TYPE == 'db':
            p_amenities = [a.id for a in p.amenities]
        else:
            p_amenities = p.amenities
        if all([a in p_amenities for a in amenities]):
            places_amenities.append(p)
    return jsonify([p.to_json() for p in places_amenities])
