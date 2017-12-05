<script>
$(document).ready(function() {
    $(document).on('click', '.add_search_field', function() {
        $search_field_parameters = $(this).closest('.search_field_parameters')

        $search_field = $search_field_parameters.clone();

        $search_field.find('*').removeClass('modified');
        $search_field_parameters.after($search_field);
    });

    $(document).on('click', '.remove_search_field', function() {
        if ($('.search_field_parameters').length < 2)
            return
        $(this).closest('.search_field_parameters').remove();
    });

    var isSearchFieldChanged = false;

    //CHANGED FIELDS CHECKER
    $(document).on('change keyup paste', '#search_fields_container input, select', function(e) {
        $(this).addClass('modified')
        isSearchFieldChanged = true
    });

    //CATCH USER
    $('a').on('click', function(e) {
        if (isSearchFieldChanged) {
            $that = $(this)
            e.preventDefault();
            $('#modal-notsaved').modal();

            var proceed_leave = function() {
                console.log('bye');
                window.location = $that.attr('href');
            };

            $('#confirm_leave').on('click', proceed_leave);

            $('#modal-notsaved').one('hidden.bs.modal', function () {
                $('#confirm_leave').off('click', proceed_leave);
            });
        }
    });

    //ACTION LINKS
//    $(document).on('click', '.record-action-link', function(e) {
//        e.preventDefault();
//        window.open($(this).attr('href'));
//    });
});
</script>