from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from . import VoiceLabel
from .vs_element import VoiceServiceElement
from .vse_choice import Choice
from .voiceservice import VoiceService


class Report(VoiceServiceElement):
    """An element that bundles choices and recordings made by the user to store
    them in the database.

    Plays a summary of the choices that will be stored and asks the user if
    they want to confirm yes or no. Based on this choice, two different
    redirects are possible."""

    _urls_name = 'service-development:report'

    ask_confirmation_voice_label = models.ForeignKey(
        VoiceLabel,
        verbose_name=_('Ask for confirmation voice label'),
        help_text=_('The voice label that asks the user to confirm their report. Example: "Do you want to submit this \
            report? Press 1 to confirm and submit, or press 2 to discard this report."'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    _redirect_yes = models.ForeignKey(
        VoiceServiceElement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Redirect element yes'),
        help_text=_("The element to redirect to if the user chooses to submit the report."),
        related_name='reports_yes_redirect'
    )

    _redirect_no = models.ForeignKey(
        VoiceServiceElement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Redirect element no'),
        help_text=_("The element to redirect to if the user chooses not to submit the report."),
        related_name='reports_no_redirect'
    )

    class Meta:
        verbose_name = _('Report Element')

    @property
    def redirect_yes(self):
        """
        Returns the actual subclassed object that is redirected to after submission,
        instead of the VoiceServiceElement superclass object (which does
        not have specific fields and methods).
        """
        if self._redirect_yes:
            return VoiceServiceElement.objects.get_subclass(id=self._redirect_yes.id)
        else:
            return None

    @property
    def redirect_no(self):
        """
        Returns the actual subclassed object that is redirected to after submission,
        instead of the VoiceServiceElement superclass object (which does
        not have specific fields and methods).
        """
        if self._redirect_no:
            return VoiceServiceElement.objects.get_subclass(id=self._redirect_no.id)
        else:
            return None

    def __str__(self):
        return "Report: " + self.name

    def is_valid(self):
        return len(self.validator()) == 0
    is_valid.boolean = True
    is_valid.short_description = _('Is valid')

    def validator(self):
        errors = []
        errors.extend(super(Report, self).validator())
        if not self._redirect_yes:
            errors.append(ugettext('Report %s does not have a redirect element for "yes"') % self.name)
        if not self._redirect_no:
            errors.append(ugettext('Report %s does not have a redirect element for "no"') % self.name)
        return errors


class ReportContent(models.Model):
    parent = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='report_contents'
    )

    content = models.ForeignKey(
        VoiceServiceElement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    service = models.ForeignKey(
        VoiceService,
        on_delete=models.CASCADE,
        help_text=_("The service to which this element belongs")
    )
    creation_date = models.DateTimeField(
        _('Date created'),
        auto_now_add=True
    )
    modification_date = models.DateTimeField(
        _('Date last modified'),
        auto_now=True
    )
    name = models.CharField(
        _('Name'),
        max_length=100
    )
    description = models.CharField(
        max_length=1000,
        blank=True
    )
    voice_label = models.ForeignKey(
        VoiceLabel,
        verbose_name=_('Voice label'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Report Content')

    def __str__(self):
        return "(%s): %s" % (self.parent.name,  self.name)

    def is_valid(self):
        return len(self.validator()) == 0
    is_valid.boolean = True
    is_valid.short_description = _('Is valid')

    def validator(self):
        return [hasattr(self.content, 'Record') or hasattr(self.content, 'Choice')]


class RetrieveReports(VoiceServiceElement):
    """An element that retrieves historic reports from the database.

    Only reports that match the selected options by the user for some predefined questions are retrieved.
    See the filter class below."""

    _urls_name = 'service-development:report'

    _redirect = models.ForeignKey(
        VoiceServiceElement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Redirect element'),
        help_text=_("The element to redirect to after playing the reports to the user"),
        related_name="retrieve_reports_redirects"
    )

    no_reports_voice_label = models.ForeignKey(
        VoiceLabel,
        verbose_name=_('No reports available voice lable'),
        help_text=_('The voice label that tells the user that there are no existing reports in the database which \
            correspond to their selected options for the choices below. Example: "Sorry, no reports exist for your \
            selected company and region."'),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    pre_report_voice_label = models.ForeignKey(
        VoiceLabel,
        verbose_name=_('Pre report voice label'),
        help_text=_('The voice label that is played before each report, will be followed by a counter. \
            Example: "Report.."'),
        on_delete=models.SET_NULL,
        related_name="retrieve_reports_pre_report_labels",
        null=True,
        blank=True,
    )

    max_amount = models.IntegerField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9')],
        default=5,
        verbose_name=_('Maximum amount of reports to retrieve')
    )

    report_element = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        verbose_name=_('Report element'),
        help_text=_("The report element for which the reports should be retrieved"),
        related_name="retrieve_reports_elements"
    )

    class Meta:
        verbose_name = _('Retrieve Reports Element')

    @property
    def redirect(self):
        """
        Returns the actual subclassed object that is redirected to after submission,
        instead of the VoiceServiceElement superclass object (which does
        not have specific fields and methods).
        """
        if self._redirect:
            return VoiceServiceElement.objects.get_subclass(id=self._redirect.id)
        else:
            return None

    def __str__(self):
        return "Retrieve reports: " + self.name

    def is_valid(self):
        return len(self.validator()) == 0
    is_valid.boolean = True
    is_valid.short_description = _('Is valid')

    def validator(self):
        errors = []
        errors.extend(super(Report, self).validator())
        if not self._redirect:
            errors.append(ugettext('Report %s does not have a redirect element for "yes"') % self.name)
        return errors


class RetrieveReportsFilter(models.Model):
    """Specifies the choice elements that should be used as a filter when retrieving
    user reports.

    Only reports with the same choice options as the current user has selected for these choices will be retrieved."""
    parent = models.ForeignKey(
        RetrieveReports,
        on_delete=models.CASCADE,
        related_name="choices_filter"
    )

    choice_element = models.ForeignKey(
        Choice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Only reports that have the same option selected for this choice as in the current session will \
            be retrieved")
    )

    service = models.ForeignKey(
        VoiceService,
        on_delete=models.CASCADE,
        help_text=_("The service to which this element belongs")
    )
    creation_date = models.DateTimeField(
        _('Date created'),
        auto_now_add=True
    )
    modification_date = models.DateTimeField(
        _('Date last modified'),
        auto_now=True
    )
    name = models.CharField(
        _('Name'),
        max_length=100
    )
    description = models.CharField(
        max_length=1000,
        blank=True
    )

    class Meta:
        verbose_name = _('Report Content')

    def __str__(self):
        return "(%s): %s" % (self.parent.name,  self.name)

    def is_valid(self):
        return len(self.validator()) == 0
    is_valid.boolean = True
    is_valid.short_description = _('Is valid')

    def validator(self):
        return [hasattr(self.content, 'Record') or hasattr(self.content, 'Choice')]
