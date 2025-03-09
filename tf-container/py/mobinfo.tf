/set warn_curly_re=off

/set batmud_regmons=[38;2;80;255;80m ;; #50FF50
/set batmud_aggrmons=[38;2;255;80;80m ;; #FF5050
/set batmud_woundedmons=[38;2;80;208;80m ;;
/set batmud_woundedaggrmons=[38;2;208;80;80m

/def -i -F -p2 -mregexp -t"^[A-z(].+" monster_exp_substitution = \
    /let enc=$[substr(encode_ansi({*}), 1)]%; \
    /if (strncmp(batmud_regmons, enc, 16) == 0) \
        /substitute %{*} (regmons)%;\
    /elseif (strncmp(batmud_woundedmons, enc, 16) == 0) \
        /substitute %{*} (woundedmons)%;\
    /elseif (strncmp(batmud_aggrmons, enc, 16) == 0) \
        /substitute %{*} (aggrmons)%;\
    /elseif (strncmp(batmud_woundedaggrmons, enc, 16) == 0) \
        /substitute %{*} (woundedaggrmons)%;\
    /endif

/def -i -msimple -t"a wealthy-looking armourer" monster_exp_substitution_test = \
    /let enc=$[substr(encode_ansi({*}), 1)]%; \
    /echo %{enc}
