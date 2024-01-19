test:
	dzil test

pod_test:
	prove -lv t/*pod*.t

tidy:
	find . -name '*.p?.bak' -delete
	find . -not -path "./.git*" -name '*.p[lm]' -o -name '*.t' | xargs perltidier -pro=./t/rc/perltidyrc --backup-and-modify-in-place -bext=tidyup
	find . -name '*.tidyup' -delete
