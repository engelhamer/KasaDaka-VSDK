from django.shortcuts import render, get_object_or_404

from ..models import lookup_or_create_session
from ..models import CallSessionChoice
from ..models import CallSessionStep
from ..models import ReportContent
from ..models import RetrieveReports


def get_reports(retrieve_element, session):
    # Ignore any input that has been entered before the last time the voice service's start
    # element has been visited for this session. This allows for report elements even when the
    # user has the ability to restart the service instead of terminating the call at some point.
    iteration_start_time = CallSessionStep.objects.filter(
        session=session,
        _visited_element=session.service.start_element
    ).latest('time').time

    user_reports = retrieve_element.report_element.user_reports
    filter_choices_selected = []

    for choice_filter in retrieve_element.choices_filter.all():
        stored_choice = CallSessionChoice.objects.filter(
            session=session,
            choice_element=choice_filter.choice_element,
            time__gte=iteration_start_time
        )
        if stored_choice.exists():
            choice_option_selected = stored_choice.latest('time').choice_option_selected
            filter_choices_selected.append({
                'voice_label': ReportContent.objects.get(
                    parent=retrieve_element.report_element,
                    content=choice_option_selected.parent
                ).voice_label.get_voice_fragment_url(session.language),
                'value': choice_option_selected.voice_label.get_voice_fragment_url(session.language)
            })
            user_reports = user_reports.filter(
                choices__choice_option_selected=choice_option_selected
            )

    user_reports = user_reports.order_by('-time')[:retrieve_element.max_amount]
    voice_reports = []
    for user_report in user_reports:
        voice_report_content = []
        for choice in user_report.choices.exclude(choice_element__in=retrieve_element.choices_filter.values(
                'choice_element')):
            voice_report_content.append({
                'voice_label': ReportContent.objects.get(
                    parent=retrieve_element.report_element,
                    content=choice.choice_element
                ).voice_label.get_voice_fragment_url(session.language),
                'value': choice.choice_option_selected.voice_label.get_voice_fragment_url(session.language)
            })
        for recording in user_report.recordings.all():
            voice_report_content.append({
                'voice_label': ReportContent.objects.get(
                    parent=retrieve_element.report_element,
                    content=recording.record_element
                ).voice_label.get_voice_fragment_url(session.language),
                'value': recording.get_voice_fragment_url(),
            })
        voice_reports.append(voice_report_content)

    return filter_choices_selected, voice_reports


def retrieve_reports_generate_context(request, retrieve_element, session):
    language = session.language

    voice_label = retrieve_element.voice_label.get_voice_fragment_url(language)
    pre_report_voice_label = retrieve_element.pre_report_voice_label.get_voice_fragment_url(language)
    no_reports_voice_label = retrieve_element.no_reports_voice_label.get_voice_fragment_url(language)

    filter_choices_selected, reports = get_reports(retrieve_element, session)

    context = {
        'voice_label': voice_label,
        'pre_report_voice_label': pre_report_voice_label,
        'no_reports_voice_label': no_reports_voice_label,
        'numbers': language.get_interface_numbers_voice_label_url_list,
        'filter_choices_selected': filter_choices_selected,
        'reports': reports,
        'redirect_url': retrieve_element.redirect.get_absolute_url(session)
    }

    return context


def retrieve_reports(request, element_id, session_id):
    retrieve_element = get_object_or_404(RetrieveReports, pk=element_id)
    voice_service = retrieve_element.service
    session = lookup_or_create_session(voice_service, session_id)

    session.record_step(retrieve_element)
    context = retrieve_reports_generate_context(request, retrieve_element, session)

    return render(request, 'retrieve_reports.xml', context, content_type='text/xml')
