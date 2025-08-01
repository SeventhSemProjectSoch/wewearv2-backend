from django import forms
from django.db import models


class DataListForm(forms.ModelForm):
    model_field_tuple: list[tuple[type, str]] = []

    class Meta:
        model: None | models.Model = None
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for model, field in self.model_field_tuple:
            existing_body_types = model.objects.values_list("name", flat=True)
            self.fields[field].widget = forms.TextInput()
            self.fields[field].widget.attrs.update(
                {
                    "list": f"{field}_list",
                    "autocomplete": " ".join([i for i in existing_body_types]),
                }
            )
            self.Meta.model = model
