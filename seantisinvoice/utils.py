def formatThousands(s, tSep="'", dSep='.'):
    s = str(s)
    if s.rfind('.')>0:
        rhs=s[s.rfind('.')+1:]
        s=s[:s.rfind('.')]
        if len(s) <= 3: 
            return s + dSep + rhs
        return formatThousands(s[:-3], tSep) + tSep + s[-3:] + dSep + rhs
    else:
        if len(s) <= 3: 
            return s
        return formatThousands(s[:-3], tSep) + tSep + s[-3:]
