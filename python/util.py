import json
from Flask import Response

# Adds a default serializer for datetime objects, which python doesn't know how
# to json serialize by default; note: this still allows everything else to be
# serialized just fine!
def json_ser_with_datetime(obj):
	import calendar, datetime

	if isinstance(obj, datetime.datetime):
		if obj.utcoffset() is not None:
			obj = obj - obj.utcoffset()

	millis = int(
		calendar.timegm(obj.timetuple()) * 1000 +
		obj.microsecond / 1000
	)

	return millis

def json_response(obj):
	return Response(
			json.dumps(obj, 
				default = json_ser_with_datetime,
				indent = 4,
				separators=(',', ': ')
				),
			mimetype="application/json"
			)
