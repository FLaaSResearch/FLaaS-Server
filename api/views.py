import os

from api.models import Project, DeviceTrainRequest, DeviceStatusResponse, Round, JoinedRounds
from api.serializers import ProjectSerializer, RoundSerializer  # , DeviceResponseSerializer

from django.utils import timezone
from django.http import Http404, HttpResponseRedirect
from django.core.files.storage import default_storage

from rest_framework.exceptions import ParseError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import FileUploadParser
from rest_framework import status
from rest_framework import renderers
from rest_framework.permissions import IsAuthenticated

from api.libs import consts
from api.mlreport import MLReport


class ProjectList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)


class ProjectDetail(APIView):
    permission_classes = (IsAuthenticated,)

    def get_project(self, project_id):
        try:
            return Project.objects.get(pk=project_id)

        except Project.DoesNotExist:
            raise Http404

    def get(self, request, project_id):
        project = self.get_project(project_id)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)


class ModelRenderer(renderers.BaseRenderer):
    media_type = 'application/octet-stream'
    format = 'bin'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class ModelUploadParser(FileUploadParser):
    media_type = 'application/octet-stream'


class GetSamples(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = [ModelRenderer]

    def get(self, request, dataset_type, app):

        # Get device (should have used a serializer)
        device = request.user.profile.device
        samples_index = device.samples_index

        file = os.path.join(consts.SAMPLES_PATH, dataset_type, str(samples_index), str(app), consts.SAMPLES_FILENAME)
        if default_storage.exists(file):
            url = default_storage.url(file)
            return HttpResponseRedirect(url)
            # with default_storage.open(file) as data:
            #     return Response(
            #         data.read(),
            #         headers={'Content-Disposition': 'attachment; filename="%s"' % consts.SAMPLES_FILENAME})

        else:
            raise Http404


class GetModel(APIView):
    permission_classes = (IsAuthenticated,)
    renderer_classes = [ModelRenderer]

    def get_project(self, project_id):
        try:
            return Project.objects.get(pk=project_id)

        except Project.DoesNotExist:
            raise Http404

    def get(self, request, project_id, round):

        # not needed, just to check that project exists
        self.get_project(project_id)

        file = os.path.join(consts.PROJECTS_PATH, str(project_id), str(round), consts.MODEL_WEIGHTS_FILENAME)
        if default_storage.exists(file):
            url = default_storage.url(file)
            return HttpResponseRedirect(url)
            # with default_storage.open(file) as data:
            #     return Response(
            #         data.read(),
            #         headers={'Content-Disposition': 'attachment; filename="%s"' % consts.MODEL_WEIGHTS_FILENAME})

        else:
            raise Http404


class JoinRound(APIView):
    permission_classes = (IsAuthenticated,)

    def get_project(self, project_id):
        try:
            return Project.objects.get(pk=project_id)

        except Project.DoesNotExist:
            raise Http404

    def get_round(self, project, round_number):
        try:
            return Round.objects.get(
                project=project,
                round_number=round_number)

        except Project.DoesNotExist:
            raise Http404

    def get(self, request, project_id, round):

        # get project
        project = self.get_project(project_id)

        # get status param (if available, if not get JOIN_ROUND)
        status = request.query_params.get("status", JoinedRounds.Status.JOIN_ROUND)

        # join round
        round_model = self.get_round(project, round)
        device = request.user.profile.device

        # check if already joined
        try:
            joinedRounds = JoinedRounds.objects.get(round=round_model, device=device)
            joinedRounds.status = status
            joinedRounds.date_last_state = timezone.now()
            joinedRounds.save()

        except JoinedRounds.DoesNotExist:
            joinedRounds = None

        # if not joined
        if not joinedRounds:

            # create object
            JoinedRounds.objects.create(
                round=round_model,
                device=device,
                status=status)

        serializer = RoundSerializer(round_model)
        return Response(serializer.data)


class ReportAvailibility(APIView):
    permission_classes = (IsAuthenticated,)

    # def get_project(self, id):
    #     try:
    #         return Project.objects.get(pk=id)

    #     except Project.DoesNotExist:
    #         raise Http404

    def get_device_train_request(self, request_id):
        try:
            return DeviceTrainRequest.objects.get(pk=request_id)

        except DeviceTrainRequest.DoesNotExist:
            raise Http404

    def post(self, request):

        # Get device (should have used a serializer)
        device = request.user.profile.device

        # print(request.data)  # debug
        request_type = request.data.get('request_type')
        device_info = request.data.get('device_info')
        if device_info is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Save device details
        device_details = device_info.get("device_details")
        if device_details is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        device.model = device_details.get("model")
        device.os_version = device_details.get("os_version")
        device.manufacturer = device_details.get("manufacturer")
        device.brand = device_details.get("brand")
        device.build_type = device_details.get("type")
        device.incremental = device_details.get("incremental")
        device.os = device_details.get("os")
        device.os_version = device_details.get("version")
        device.security_patch = device_details.get("security_patch")
        device.save()

        # if train request, get the associated model (else none)
        if request_type == "device-ping":
            device_train_request = None

        elif request_type == "device-train":
            request_id = request.data.get('request_id')
            if request_id is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            device_train_request = self.get_device_train_request(request_id)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # create the object in the db
        DeviceStatusResponse.objects.create(
            device=device,
            device_train_request=device_train_request,
            data=device_info)

        return Response(status=status.HTTP_201_CREATED)


class ResultsUploadParser(FileUploadParser):
    media_type = 'application/json'


class SubmitResults(APIView):
    permission_classes = (IsAuthenticated,)
    # renderer_classes = [ModelRenderer]
    parser_classes = (ResultsUploadParser,)

    def get_project(self, project_id):
        try:
            return Project.objects.get(pk=project_id)

        except Project.DoesNotExist:
            raise Http404

    def post(self, request, project_id, round, filename):

        project = self.get_project(project_id)
        device_id = request.user.profile.device.id

        if 'file' not in request.data:
            raise ParseError("Empty content")

        # session level
        path = os.path.join(consts.PROJECTS_PATH, str(project.id), str(round), str(device_id))

        # save file
        file = request.data['file']
        default_storage.save(os.path.join(path, file.name), file)

        return Response(status=status.HTTP_201_CREATED)


class SubmitModel(APIView):
    permission_classes = (IsAuthenticated,)
    # renderer_classes = [ModelRenderer]
    parser_classes = (ModelUploadParser,)

    def get_project(self, project_id):
        try:
            return Project.objects.get(pk=project_id)

        except Project.DoesNotExist:
            raise Http404

    def post(self, request, project_id, round, filename):

        project = self.get_project(project_id)
        device_id = request.user.profile.device.id

        if 'file' not in request.data:
            raise ParseError("Empty content")

        # session level
        path = os.path.join(consts.PROJECTS_PATH, str(project.id), str(round), str(device_id))

        # save file
        file = request.data['file']
        default_storage.save(os.path.join(path, file.name), file)

        return Response(status=status.HTTP_201_CREATED)


class ComputePerformance(APIView):

    def post(self, request):
        # print(request.data)  # debug

        # check if data are available
        results = request.data
        if results is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # compute report (accuracy for now)
        report = MLReport(results['ytrue'], results['ypred'])

        # create respnse
        response = {
            "accuracy": report.get_accuracy(),
            # "precision": report.get_precision(),
            # "f1_score": report.get_f1_score()
        }

        # repond with data
        return Response(response)
