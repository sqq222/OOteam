from rest_framework.renderers import JSONRenderer


class ImageJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response_data = {}
        # object_list = 'results'
        # try:
        #     meta_dict = getattr(renderer_context.get('view').get_serializer().Meta, 'meta_dict')
        # except:
        #     meta_dict = dict()
        # try:
        #     data.get('paginated_results')
        #     response_data['meta'] = data['meta']
        #     response_data[object_list] = data
        # except:
        #     response_data[object_list] = data
        #     response_data['meta'] = dict()
        #     # Add custom meta data
        #     response_data['meta'].update(meta_dict)
        #     # Call super to render the response
        response = super(ImageJSONRenderer, self).render(data, accepted_media_type, renderer_context)
        return data
