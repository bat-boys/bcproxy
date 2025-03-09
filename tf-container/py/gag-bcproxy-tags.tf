/def -i -F -mregexp -p21 -t"^(spec_[a-z]+: )" bcproxy_spec = /substitute %-1
/def -i -F -mregexp -p21 -t"^(chan_[a-z]+: )" bcproxy_chan = /substitute %-1
/def -i -mglob -agGL -p20 -t"\\\∴*" bcproxy_gag
/def -i -mglob -agGL -p20 -t"\\\∴hpstatus*" bcproxy_gag_hpstatus
