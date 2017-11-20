<script>
$(document).ready(function() {
    $(document).on('click', '.add_search_field', function() {
        $search_field_parameters = $(this).closest('.search_field_parameters')
        $search_field_parameters.after($search_field_parameters.clone());
        console.log($(this).closest('#search_field_parameters'));
    });

    $(document).on('click', '.remove_search_field', function() {
        if ($('.search_field_parameters').length < 2)
            return
        $(this).closest('.search_field_parameters').remove();
    });
});
</script>