test:
	dzil test && dzil xtest

install:
	dzil run cpanm --force -l /home/git/regentmarkets/cpan-private/local .

pod_test:
	prove -lv t/*pod*.t

tidy:
	dzil perltidy && git checkout -- Makefile.PL
