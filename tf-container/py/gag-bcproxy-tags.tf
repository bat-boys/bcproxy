/def -i -F -mregexp -p21 -t"^(spec_[a-z]+: )" bcproxy_spec = /substitute %-1
/def -i -F -mregexp -p21 -t"^(chan_[a-z]+: )" bcproxy_chan = /substitute %-1
/def -i -F -mglob -agGL -p1 -t"\\\∴*" bcproxy_gag
