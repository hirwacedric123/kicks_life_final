'use strict';
{
    const RWF = django.jQuery;
    const fields = RWF('#django-admin-prepopulated-fields-constants').data('prepopulatedFields');
    RWF.each(fields, function(index, field) {
        RWF(
            '.empty-form .form-row .field-' + field.name +
            ', .empty-form.form-row .field-' + field.name +
            ', .empty-form .form-row.field-' + field.name
        ).addClass('prepopulated_field');
        RWF(field.id).data('dependency_list', field.dependency_list).prepopulate(
            field.dependency_ids, field.maxLength, field.allowUnicode
        );
    });
}
