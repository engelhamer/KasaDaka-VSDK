from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect

from ..models import *


def choice_options_resolve_voice_labels(choice_options, language):
    """
    Returns a list of voice labels belonging to the provided list of choice_options.
    """
    choice_options_voice_labels = []
    for choice_option in choice_options:
        choice_options_voice_labels.append(choice_option.get_voice_fragment_url(language))
    return choice_options_voice_labels

def choice_generate_context(request, choice_element, session):
    """
    Returns a dict that can be used to generate the choice VXML template
    choice = this Choice element object
    choice_voice_label = the resolved Voice Label URL for this Choice element
    choice_options = iterable of ChoiceOption object belonging to this Choice element
    choice_options_voice_labels = list of resolved Voice Label URL's referencing to the choice_options in the same position
    choice_options_redirect_urls = list of resolved redirection URL's referencing to the choice_options in the same position
        """
    choice_options = choice_element.choice_options.all()
    language = session.language
    context = {
        'choice': choice_element,
        'choice_voice_label': choice_element.get_voice_fragment_url(language),
        'choice_options': choice_options,
        'choice_options_voice_labels': choice_options_resolve_voice_labels(choice_options, language),
        'choice_options_ids': [choice_option.pk for choice_option in choice_options],
        'language': language,
        'url': request.get_full_path(False)
    }
    return context


def choice(request, element_id, session_id):
    choice_element = get_object_or_404(Choice, pk=element_id)
    session = get_object_or_404(CallSession, pk=session_id)

    if request.method == "POST":
        choice_option_selected = get_list_or_404(ChoiceOption, pk=request.option_id)
        session.record_choice(choice_element, choice_option_selected)

        return redirect(choice_option_selected.redirect.get_absolute_url(session))

    session.record_step(choice_element)
    context = choice_generate_context(request, choice_element, session)

    return render(request, 'choice.xml', context, content_type='text/xml')

