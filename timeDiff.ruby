#!/usr/bin/ruby
require "Time"
def time_diff(time1_str, time2_str)
  t = Time.at( Time.parse(time2_str) - Time.parse(time1_str) )
  (t - t.gmt_offset).strftime("%H:%M:%S.%L")
end

print time_diff(ARGV[0], ARGV[1])
