from tzwhere import tzwhere

# We load the tz structure once when Idunn starts since it's a time consuming step
tz = tzwhere.tzwhere(forceTZ=True)
