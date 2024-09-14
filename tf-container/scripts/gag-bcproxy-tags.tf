/def -i -F -mregexp -p100 -t"^(spec_[a-z]+: )" bcproxy_spec = /substitute %-1
/def -i -F -mregexp -p100 -t"^(chan_[a-z]+: )" bcproxy_chan = /substitute %-1
/def -i -F -mglob -agGL -p5 -t"\\\∴*" bcproxy_gag
