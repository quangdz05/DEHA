from django import forms
from django.utils import timezone
from gym_booking_backend.infrastructure.models import PTPackage, Trainer
from gym_booking_backend.domain.constants import WeekdayChoices


class MonthlyPTBookingForm(forms.Form):
    package = forms.ModelChoiceField(
        queryset=PTPackage.objects.filter(is_active=True),
        empty_label="-- Chọn gói PT --",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    trainer = forms.ModelChoiceField(
        queryset=Trainer.objects.filter(status="active"),
        empty_label="-- Chọn Huấn luyện viên --",
        widget=forms.Select(attrs={"class": "form-select"})
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    weekdays = forms.MultipleChoiceField(
        choices=WeekdayChoices.choices,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=True
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"})
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={"class": "form-control", "type": "time"})
    )
    note = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Ghi chú thêm cho PT..."}),
        required=False
    )

    def clean_start_date(self):
        start_date = self.cleaned_data.get("start_date")
        if start_date and start_date < timezone.localdate():
            raise forms.ValidationError("Ngày bắt đầu không được nhỏ hơn ngày hôm nay.")
        return start_date

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError("Giờ bắt đầu phải trước giờ kết thúc.")

        return cleaned_data
