from django.shortcuts import render, get_object_or_404, redirect

from ..models import VoiceServiceElement
from ..models import Record
from ..models import SpokenUserInput
from ..models import lookup_or_create_session
from ..models import Choice
from ..models import CallSessionChoice
from ..models import Report
from ..models import UserReport


def report_get_redirect_no_url(report_element, session):
    return report_element.redirect_no.get_absolute_url(session)


def report_get_summary(report_element, session):
    # TODO: alleen als deze later is dan de laatste visit van het startpunt (Welcome to vacarpa) dan toevoegen
    summary = []
    for report_content in report_element.report_contents.all():
        element = VoiceServiceElement.objects.get_subclass(id=report_content.content.id)
        if isinstance(element, Record):
            recorded_input = SpokenUserInput.objects.filter(
                session=session,
                record_element=element
            )
            if recorded_input.exists():
                summary.append({
                    'voice_label': report_content.voice_label.get_voice_fragment_url(session.language),
                    'value': recorded_input.latest('time').get_voice_fragment_url(),
                })
        elif isinstance(element, Choice):
            stored_choice = CallSessionChoice.objects.filter(
                session=session,
                choice_element=element
            )
            if stored_choice.exists():
                summary.append({
                    'voice_label': report_content.voice_label.get_voice_fragment_url(session.language),
                    'value': stored_choice.latest('time').choice_option_selected.voice_label
                                          .get_voice_fragment_url(session.language),
                })

    return summary


def report_generate_context(request, report_element, session):
    language = session.language
    redirect_no_url = report_get_redirect_no_url(report_element, session)

    voice_label = report_element.voice_label.get_voice_fragment_url(language)
    ask_confirmation_voice_label = report_element.ask_confirmation_voice_label.get_voice_fragment_url(language)

    summary = report_get_summary(report_element, session)

    context = {
        'report': report_element,
        'redirect_no_url': redirect_no_url,
        'voice_label': voice_label,
        'ask_confirmation_voice_label': ask_confirmation_voice_label,
        'summary': summary,
        'url': request.get_full_path(False)
    }

    return context


def report(request, element_id, session_id):
    report_element = get_object_or_404(Report, pk=element_id)
    voice_service = report_element.service
    session = lookup_or_create_session(voice_service, session_id)

    if request.method == "POST":
        new_report = UserReport()
        new_report.session = session
        new_report.save()

        for report_content in report_element.report_contents.all():
            element = VoiceServiceElement.objects.get_subclass(id=report_content.content.id)
            if isinstance(element, Record):
                recording_or_choice = SpokenUserInput.objects.filter(
                    session=session,
                    record_element=element
                )
            elif isinstance(element, Choice):
                recording_or_choice = CallSessionChoice.objects.filter(
                    session=session,
                    choice_element=element
                )
            if recording_or_choice.exists():
                recording_or_choice = recording_or_choice.latest('time')
                recording_or_choice.report = new_report
                recording_or_choice.save()

        return redirect(report_element.redirect_yes.redirect.get_absolute_url(session))

    session.record_step(report_element)
    context = report_generate_context(request, report_element, session)

    return render(request, 'report.xml', context, content_type='text/xml')
