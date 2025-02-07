from django.shortcuts import render, redirect
from django.contrib.auth import authenticate
from .models import (StudentProfile, TeacherProfile, Internship, Project, Committee, ResearchPaper, BeProject,
                     Hackathon, Skill, Education, ExtraCurricular, KT, Subject, SubjectMarks, TermTest,
                     CompetitiveExams, Admit)
from .models import (HistoricalInternship, HistoricalProject, HistoricalCommittee, HistoricalResearchPaper,
                     HistoricalBeProject, HistoricalHackathon, HistoricalEducation, HistoricalExtraCurricular)
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage
from .tokens import account_activation_token
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
import collections
from django.utils.dateformat import format
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from datetime import timedelta
import os
import requests


def homepage(request):
    return render(request, 'index.html')


def show_rollingform(request):
    return render(request, 'user_profile/edit_student_profile.html')


def register(request):
    if request.user.is_authenticated:
        student_profile = StudentProfile.objects.get(student=request.user)
        student_profile_url = '/student_profile/' + str(student_profile.id)
        return HttpResponseRedirect(student_profile_url)
    else:
        mentor_list = TeacherProfile.objects.all()
        if request.method == 'POST':
            username = request.POST.get('Sap_Id', '')
            password = request.POST.get('password', '')
            email = request.POST.get('email', '')
            mentor = request.POST.get('mentor', '')
            Sap_Id = request.POST.get('Sap_Id', '')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')

            if User.objects.filter(username=username).exists():
                error = 'The Sap_id is already in use by another account.'
                return render(request, 'user_profile/registration.html', {'error': error,'mentor_list':mentor_list})
            elif len(Sap_Id)<11:
                error = 'The Sap_id should be 11 digits long.'
                return render(request, 'user_profile/registration.html', {'error': error,'mentor_list':mentor_list})
            elif len(password)<8:
                error = 'The Password should be 8 characters long.'
                return render(request, 'user_profile/registration.html', {'error': error,'mentor_list':mentor_list})
            elif mentor=='':
                error = 'Please choose a mentor'
                return render(request, 'user_profile/registration.html', {'error': error,'mentor_list':mentor_list})
            else:
                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.save()
                content_type = ContentType.objects.get_for_model(
                    StudentProfile)
                permission = Permission.objects.get(
                    content_type=content_type, codename='view_student')
                user.user_permissions.add(permission)
                sap = str(Sap_Id)
                mentor = TeacherProfile.objects.get(Sap_Id=int(mentor))
                student = StudentProfile.objects.create(
                    student=user, Sap_Id=Sap_Id, sap=sap, first_name=first_name,
                    last_name=last_name,mentor=mentor)
                student.save()
                auth_login(request, user)
                student_profile_url = '/student_profile/' + str(student.id)
                return HttpResponseRedirect(student_profile_url)
                # return render(request, 'user_profile/profile.html', {"student": student})
        else:
            return render(request, 'user_profile/registration.html', {'mentor_list':mentor_list})


def user_login(request):
    if request.user.is_authenticated:
        try:
            student_profile = StudentProfile.objects.get(student=request.user)
            student_profile_url = '/student_profile/' + str(student_profile.id)
            return HttpResponseRedirect(student_profile_url)
        except Exception as e:
            teacher_profile_url = '/teacherdashboard/'
            return HttpResponseRedirect(teacher_profile_url)
    else:
        if request.method == 'POST':
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    # return render(request, 'user_profile/profile.html', {})
                    try:
                        student_profile = StudentProfile.objects.get(
                            student=user)
                        auth_login(request, user)
                        student_profile_url = '/student_profile/' + \
                            str(student_profile.id)
                        return HttpResponseRedirect(student_profile_url)
                    except Exception as e:
                        teacher_profile_url = '/login/teacher/'
                        return HttpResponseRedirect(teacher_profile_url)
                else:
                    error = 'Your account is disabled.'
                    return render(request, 'user_profile/login.html', {'error': error})
            else:
                error = 'Incorrect Username or Password'
                return render(request, 'user_profile/login.html', {'error': error})
        else:
            return render(request, 'user_profile/login.html', {})


def register_teacher(request):
    if request.user.is_authenticated:
        teacher_profile_url = '/teacherdashboard/'
        return HttpResponseRedirect(teacher_profile_url)
    else:
        if request.method == 'POST':
            username = request.POST.get('Sap_Id', '')
            password = request.POST.get('password', '')
            email = request.POST.get('email', '')
            Sap_Id = request.POST.get('Sap_Id', '')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')

            if User.objects.filter(username=username).exists():
                error = 'The Sap_id is already in use by another account.'
                return render(request, 'user_profile/registration_teacher.html', {'error': error})
            elif len(Sap_Id)<11:
                error = 'The Sap_id should be 11 digits long.'
                return render(request, 'user_profile/registration_teacher.html', {'error': error})
            elif len(password)<8:
                error = 'The Password should be 8 characters long.'
                return render(request, 'user_profile/registration_teacher.html', {'error': error})
            elif email.split('@')[1] != 'djsce.ac.in':
                error = 'Please provide an email address with domain djsce.ac.in'
                return render(request, 'user_profile/registration_teacher.html', {'error': error})
            else:
                user = User.objects.create_user(username=username, email=email)
                user.set_password(password)
                user.save()
                content_type = ContentType.objects.get_for_model(
                    TeacherProfile)
                permission = Permission.objects.get(
                    content_type=content_type, codename='view_teacher')
                user.user_permissions.add(permission)
                content_type = ContentType.objects.get_for_model(
                    StudentProfile)
                permission = Permission.objects.get(
                    content_type=content_type, codename='view_student')
                user.user_permissions.add(permission)
                ct = ContentType.objects.get_for_model(StudentProfile)
                permission = Permission.objects.get(
                    codename='delete_studentprofile', content_type=ct)
                user.user_permissions.add(permission)
                ct = ContentType.objects.get_for_model(Internship)
                permission = Permission.objects.get(
                    codename='delete_internship', content_type=ct)
                user.user_permissions.add(permission)
                ct = ContentType.objects.get_for_model(Project)
                permission = Permission.objects.get(
                    codename='delete_project', content_type=ct)
                user.user_permissions.add(permission)
                ct = ContentType.objects.get_for_model(Committee)
                permission = Permission.objects.get(
                    codename='delete_committee', content_type=ct)
                user.user_permissions.add(permission)
                ct = ContentType.objects.get_for_model(ResearchPaper)
                permission = Permission.objects.get(
                    codename='delete_researchpaper', content_type=ct)
                user.user_permissions.add(permission)
                ct = ContentType.objects.get_for_model(BeProject)
                permission = Permission.objects.get(
                    codename='delete_beproject', content_type=ct)
                user.user_permissions.add(permission)
                #Email stuff
                # user.is_active = False
                # user.save()
                # current_site = get_current_site(request)
                # mail_subject = 'Activate your account on Student Info Portal'
                # message = render_to_string('user_profile/activate_email.html', {
                #     'user': user,
                #     'first_name': first_name,
                #     'last_name': last_name,
                #     'domain': current_site.domain,
                #     'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                #     'token':account_activation_token.make_token(user),
                # })
                # email_message = EmailMessage(mail_subject, message, to=[email])
                # email_message.send()
                teacher = TeacherProfile.objects.create(
                    teacher=user, Sap_Id=Sap_Id, first_name=first_name,
                    last_name=last_name)
                teacher.save()
                auth_login(request, user)
                teacher_profile_url = '/teacherdashboard/'
                return HttpResponseRedirect(teacher_profile_url)
        else:
            return render(request, 'user_profile/registration_teacher.html', {})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        auth_login(request, user)
        teacher_profile_url = '/teacherdashboard/'
        return HttpResponseRedirect(teacher_profile_url)
    else:
        return HttpResponse('Activation link is invalid!')

def user_login_teacher(request):
    if request.user.is_authenticated:
        teacher_profile_url = '/teacherdashboard/'
        return HttpResponseRedirect(teacher_profile_url)
    else:
        if request.method == 'POST':
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    try:
                        student_profile = TeacherProfile.objects.get(teacher=user)
                        auth_login(request, user)
                        teacher_profile_url = '/teacherdashboard/'
                        return HttpResponseRedirect(teacher_profile_url)
                    except Exception as e:
                        student_profile_url = '/login/student/'
                        return HttpResponseRedirect(student_profile_url)
                else:
                    error = 'Your account is disabled. Please activate your account.'
                    return render(request, 'user_profile/teacher_login.html', {'error': error})
            else:
                error = 'Incorrect Username or Password'
                return render(request, 'user_profile/teacher_login.html', {'error': error})
        else:
            return render(request, 'user_profile/teacher_login.html', {})


def logout_student(request):
    auth_logout(request)
    return redirect(reverse('user_profile:user_login'))


def logout_teacher(request):
    auth_logout(request)
    return redirect(reverse('user_profile:user_login_teacher'))


def logout_recruiter(request):
    auth_logout(request)
    return redirect(reverse('user_login_recruiter'))


def user_login_recruiter(request):
    if request.user.is_authenticated:
        return render(request, 'user_profile/recruiter.html', {})
    else:
        if request.method == 'POST':
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    auth_login(request, user)
                    return render(request, 'user_profile/recruiter.html', {})
                else:
                    error = 'Your account is disabled.'
                    return render(request, 'user_profile/login_recruiter.html', {'error': error})
            else:
                error = 'Incorrect Username or Password'
                return render(request, 'user_profile/login_recruiter.html', {'error': error})
        else:
            return render(request, 'user_profile/login_recruiter.html', {})


def student_profile(request, id):
    if request.user.is_authenticated:
        # student = get_object_or_404(StudentProfile, Sap_Id=sapid)
        # line chart of marks
        # gpa_list = [gpa for gpa in student.education.all()[0].__dict__.values()]
        try:
            logedin_user = TeacherProfile.objects.get(teacher=request.user)
            flag = 0
        except ObjectDoesNotExist:
            flag = 1
            logedin_user = StudentProfile.objects.get(student=request.user)
        if flag==1:
            student = StudentProfile.objects.get(student=request.user)
        else:
            student = StudentProfile.objects.get(id=id)
        try:
            education = Education.objects.get(student_profile=student)
            sem1gpa = education.sem1_gpa
            sem2gpa = education.sem2_gpa
            sem3gpa = education.sem3_gpa
            sem4gpa = education.sem4_gpa
            sem5gpa = education.sem5_gpa
            sem6gpa = education.sem6_gpa
            sem7gpa = education.sem7_gpa
            sem8gpa = education.sem8_gpa
            gpa_list = []
            if sem1gpa is not None:
                gpa_list.append(float(sem1gpa))
            if sem2gpa is not None:
                gpa_list.append(float(sem2gpa))
            if sem3gpa is not None:
                gpa_list.append(float(sem3gpa))
            if sem4gpa is not None:
                gpa_list.append(float(sem4gpa))
            if sem5gpa is not None:
                gpa_list.append(float(sem5gpa))
            if sem6gpa is not None:
                gpa_list.append(float(sem6gpa))
            if sem7gpa is not None:
                gpa_list.append(float(sem7gpa))
            if sem8gpa is not None:
                gpa_list.append(float(sem8gpa))

        except Education.DoesNotExist:
            gpa_list = []

        if Project.objects.filter(student_profile=student).exists():
            color = ['#f56954', '#00a65a', '#f39c12', '#00c0ef', '#3c8dbc', '#d2d6de']
            project_objects = Project.objects.filter(student_profile=student)
            projectskill_stats = [
                project.skill.skill for project in project_objects]
            projectskill_stats = dict(collections.Counter(projectskill_stats))
            project_skills = []
            i = 0
            for key, value in projectskill_stats.items():
                i = i % 6
                colors = color[i]
                i = i + 1
                project_skills.append({'label': key, 'value': value, 'color': colors, 'highlight': colors})
        else:
            project_skills = {}

        sem_labels = []
        internship = Internship.objects.filter(employee=student)
        projects = Project.objects.filter(student_profile=student)
        committe = Committee.objects.filter(employee=student)
        researchpaper = ResearchPaper.objects.filter(student=student)
        beproj = BeProject.objects.filter(student=student)
        hackathon = Hackathon.objects.filter(student_profile=student)
        skill = Skill.objects.filter(user_profile=student)
        extracurricular = ExtraCurricular.objects.filter(student=student)
        competitive = CompetitiveExams.objects.filter(student=student)
        msadmit = Admit.objects.filter(student=student)

        for x, i in enumerate(gpa_list):
            sem_labels.append("Sem " + str(x + 1))

        return render(request, 'user_profile/profile.html',
                      {'gpa_list': gpa_list, 'projectskill_stats': project_skills,
                       'internship': internship, 'projects': projects, 'committe': committe,
                       'researchpaper': researchpaper, 'beproj': beproj, 'skill': skill,
                       'hackathon': hackathon, 'student': student, 'sem_labels': sem_labels,
                       'extracurricular': extracurricular, 'flag': flag, 'logedin_user': logedin_user,
                       'competitive':competitive, 'msadmit': msadmit})
    else:
        login = '/login/student/'
        return HttpResponseRedirect(login)

def searchany(request, skillss):
    context = {}
    try:
        teacher = TeacherProfile.objects.get(teacher=request.user)
    except ObjectDoesNotExist:
        stud = '/login/student/'
        return HttpResponseRedirect(stud)
    if request.method == 'POST':
        searchquery = request.POST.get('searchany')
        # queryset=StudentProfile.objects.filter(department__trigram_similar=searchquery)
        dept_vector = SearchVector('first_name', 'last_name', 'department', 'bio', 'year', 'mobileNo', 'github_id', 'sap')
        skill_vector = SearchVector('skill')
        hackathon_vector = SearchVector('CompetitionName', 'Desc', 'URL')
        internship_vector = SearchVector('company', 'Position', 'Loc', 'desc')
        project_vector = SearchVector('ProjName', 'ProjURL', 'ProjDesc')
        beproject_vector = SearchVector('ProjName', 'ProjURL', 'ProjDesc')
        researchpaper_vector = SearchVector('Title', 'Publication', 'Desc', 'LinkToPaper')
        committee_vector = SearchVector('OrganisationName', 'YourPosition', 'Desc')
        extracurricular_vector = SearchVector('name', 'desc', 'achievements')
        # bio_vector = SearchVector('bio')
        result = list(StudentProfile.objects.annotate(
            search=dept_vector).filter(search=searchquery))
        skills = Skill.objects.annotate(
            search=skill_vector).filter(search=searchquery)
        result.extend(list(StudentProfile.objects.filter(skill__in=skills).distinct()))
        hackathons = Hackathon.objects.annotate(
            search=hackathon_vector).filter(search=searchquery)
        result.extend(list(StudentProfile.objects.filter(hackathon__in=hackathons).distinct()))
        internships = Internship.objects.annotate(
            search=internship_vector).filter(search=searchquery)
        result.extend(list(StudentProfile.objects.filter(internships__in=internships).distinct()))
        projects = list(Project.objects.annotate(
            search=project_vector).filter(search=searchquery))
        result.extend(list(StudentProfile.objects.filter(projects__in=projects).distinct()))
        beprojects = BeProject.objects.annotate(
            search=beproject_vector).filter(search=searchquery)
        projects.extend(list(Project.objects.filter(skill__in=skills)))
        result.extend(list(StudentProfile.objects.filter(beprojects__in=beprojects).distinct()))
        researchpapers = ResearchPaper.objects.annotate(
            search=researchpaper_vector).filter(search=searchquery)
        result.extend(list(StudentProfile.objects.filter(researchpaper__in=researchpapers).distinct()))
        committees = Committee.objects.annotate(
            search=committee_vector).filter(search=searchquery)
        result.extend(list(StudentProfile.objects.filter(committee__in=committees).distinct()))
        extracurricular = ExtraCurricular.objects.annotate(
            search=extracurricular_vector).filter(search=searchquery)
        result.extend(list(StudentProfile.objects.filter(extracurricular__in=extracurricular).distinct()))
        # StudentProfile.objects.annotate(search=skill_vector).filter(search=searchquery)
        context['result'] = result
        context['skills'] = skillss
        context['hackathons'] = hackathons
        context['internships'] = internships
        context['projects'] = projects
        context['beprojects'] = beprojects
        context['committees'] = committees
        context['researchpapers'] = researchpapers
        context['extracurricular'] = extracurricular
        context['teacher'] = teacher
        return render(request, 'user_profile/filter.html', context)
    else:
        return render(request, 'user_profile/filter.html', {})


def notifs(request):
    # Dictionary for storing student list with key as Sap_Id
    teacher = TeacherProfile.objects.get(teacher=request.user)
    stu = StudentProfile.objects.filter(mentor=teacher)
    # Dictionary for storing internship changes with key as Sap_Id
    listed = {}
    for student in StudentProfile.objects.filter(mentor=teacher):
        listed[student.Sap_Id] = []
        for internship in student.internships.all():
            a = []
            a.append(internship)
            cmp1 = []
            cmp2 = []
            count = 0
            c1 = internship.history.all().count()
            if c1 == 1:
                break
            for x in internship.history.all():
                b = x.history_date
                k = HistoricalInternship.objects.get(history_date=b)
                if count == 0:
                    a.append(b)
                    cmp1.append(k.company)
                    cmp1.append(k.Position)
                    cmp1.append(k.Loc)
                    cmp1.append(k.From)
                    cmp1.append(k.To)
                    cmp1.append(k.desc)
                    cmp1.append(k.Certificate)
                    cmp1.append(k.image1)
                if count == 1:
                    cmp2.append(k.company)
                    cmp2.append(k.Position)
                    cmp2.append(k.Loc)
                    cmp2.append(k.From)
                    cmp2.append(k.To)
                    cmp2.append(k.desc)
                    cmp2.append(k.Certificate)
                    cmp2.append(k.image1)
                if count == 2:
                    break
                count = count + 1
            if cmp1[0] != cmp2[0]:
                a.append('company')
            if cmp1[1] != cmp2[1]:
                a.append('Position')
            if cmp1[2] != cmp2[2]:
                a.append('Loc')
            if cmp1[3] != cmp2[3]:
                a.append('Date Joined')
            if cmp1[4] != cmp2[4]:
                a.append('Date To')
            if cmp1[5] != cmp2[5]:
                a.append('Description')
            if cmp1[6] != cmp2[6]:
                a.append('Certificate')
            if cmp1[7] != cmp2[7]:
                a.append('Screenshot')
            if len(a) != 2:
                listed[student.Sap_Id].append(a)

    # Dictionary for storing projects changes with key as Sap_Id
    projects = {}
    for student in StudentProfile.objects.all():
        projects[student.Sap_Id] = []
        for project in student.projects.all():
            a = []
            a.append(project)
            cmp1 = []
            cmp2 = []
            count = 0
            c1 = project.history.all().count()
            if c1 == 1:
                break
            for x in project.history.all():
                b = x.history_date
                k = HistoricalProject.objects.get(history_date=b)
                if count == 0:
                    a.append(b)
                    cmp1.append(k.ProjName)
                    cmp1.append(k.ProjURL)
                    cmp1.append(k.ProjDesc)
                    cmp1.append(k.image1)
                    cmp1.append(k.projectUnderTeacher)
                    cmp1.append(k.skill)
                if count == 1:
                    cmp2.append(k.ProjName)
                    cmp2.append(k.ProjURL)
                    cmp2.append(k.ProjDesc)
                    cmp2.append(k.image1)
                    cmp2.append(k.projectUnderTeacher)
                    cmp2.append(k.skill)
                if count == 2:
                    break
                count = count + 1
            if cmp1[0] != cmp2[0]:
                a.append('Project Name')
            if cmp1[1] != cmp2[1]:
                a.append('Project URL')
            if cmp1[2] != cmp2[2]:
                a.append('Project Description')
            if cmp1[3] != cmp2[3]:
                a.append('Screenshot')
            if cmp1[4] != cmp2[4]:
                a.append('Project under Teacher')
            if cmp1[5] != cmp2[5]:
                a.append('Skill')
            if len(a) != 2:
                projects[student.Sap_Id].append(a)

        # Dictionary for storing beprojects changes with key as Sap_Id
        beprojects = {}
        for student in StudentProfile.objects.all():
            beprojects[student.Sap_Id] = []
            for beproject in student.beprojects.all():
                a = []
                a.append(beproject)
                cmp1 = []
                cmp2 = []
                count = 0
                c1 = beproject.history.all().count()
                if c1 == 1:
                    break
                for x in beproject.history.all():
                    b = x.history_date
                    k = HistoricalBeProject.objects.get(history_date=b)
                    if count == 0:
                        a.append(b)
                        cmp1.append(k.ProjName)
                        cmp1.append(k.ProjURL)
                        cmp1.append(k.ProjDesc)
                        cmp1.append(k.image1)
                        cmp1.append(k.projectUnderTeacher)
                    if count == 1:
                        cmp2.append(k.ProjName)
                        cmp2.append(k.ProjURL)
                        cmp2.append(k.ProjDesc)
                        cmp2.append(k.image1)
                        cmp2.append(k.projectUnderTeacher)
                    if count == 2:
                        break
                    count = count + 1
                if cmp1[0] != cmp2[0]:
                    a.append('Project Name')
                if cmp1[1] != cmp2[1]:
                    a.append('Project URL')
                if cmp1[2] != cmp2[2]:
                    a.append('Project Description')
                if cmp1[3] != cmp2[3]:
                    a.append('Screenshot')
                if cmp1[4] != cmp2[4]:
                    a.append('Teacher')
                if len(a) != 2:
                    beprojects[student.Sap_Id].append(a)

        # Dictionary for storing committee changes with key as Sap_Id
        committee = {}
        for student in StudentProfile.objects.all():
            committee[student.Sap_Id] = []
            for committe in student.committee.all():
                a = []
                a.append(committe)
                cmp1 = []
                cmp2 = []
                count = 0
                c1 = committe.history.all().count()
                if c1 == 1:
                    break
                for x in committe.history.all():
                    b = x.history_date
                    k = HistoricalCommittee.objects.get(history_date=b)
                    if count == 0:
                        a.append(b)
                        cmp1.append(k.OrganisationName)
                        cmp1.append(k.YourPosition)
                        cmp1.append(k.Loc)
                        cmp1.append(k.dateFrom)
                        cmp1.append(k.dateTo)
                        cmp1.append(k.Desc)
                        cmp1.append(k.Certificate)
                        cmp1.append(k.image1)
                    if count == 1:
                        cmp2.append(k.OrganisationName)
                        cmp2.append(k.YourPosition)
                        cmp2.append(k.Loc)
                        cmp2.append(k.dateFrom)
                        cmp2.append(k.dateTo)
                        cmp2.append(k.Desc)
                        cmp2.append(k.Certificate)
                        cmp2.append(k.image1)
                    if count == 2:
                        break
                    count = count + 1
                if cmp1[0] != cmp2[0]:
                    a.append('Company')
                if cmp1[1] != cmp2[1]:
                    a.append('Position')
                if cmp1[2] != cmp2[2]:
                    a.append('Location')
                if cmp1[3] != cmp2[3]:
                    a.append('Date Joined')
                if cmp1[4] != cmp2[4]:
                    a.append('Date To')
                if cmp1[5] != cmp2[5]:
                    a.append('Description')
                if cmp1[6] != cmp2[6]:
                    a.append('Certificate')
                if cmp1[7] != cmp2[7]:
                    a.append('Screenshot')
                if len(a) != 2:
                    committee[student.Sap_Id].append(a)

        # Dictionary for storing ResearchPaper changes with key as Sap_Id
        researchpaper = {}
        for student in StudentProfile.objects.all():
            researchpaper[student.Sap_Id] = []
            for research in student.researchpaper.all():
                a = []
                a.append(research)
                cmp1 = []
                cmp2 = []
                count = 0
                c1 = research.history.all().count()
                if c1 == 1:
                    break
                for x in research.history.all():
                    b = x.history_date
                    k = HistoricalResearchPaper.objects.get(history_date=b)
                    if count == 0:
                        a.append(b)
                        cmp1.append(k.Title)
                        cmp1.append(k.Publication)
                        cmp1.append(k.DateOfPublication)
                        cmp1.append(k.Desc)
                        cmp1.append(k.LinkToPaper)
                        cmp1.append(k.Desc)
                        cmp1.append(k.PaperId)
                        cmp1.append(k.image1)
                        cmp1.append(k.Published_under)
                    if count == 1:
                        cmp2.append(k.Title)
                        cmp2.append(k.Publication)
                        cmp2.append(k.DateOfPublication)
                        cmp2.append(k.Desc)
                        cmp2.append(k.LinkToPaper)
                        cmp2.append(k.Desc)
                        cmp2.append(k.PaperId)
                        cmp2.append(k.image1)
                        cmp2.append(k.Published_under)
                    if count == 2:
                        break
                    count = count + 1
                if cmp1[0] != cmp2[0]:
                    a.append('Title')
                if cmp1[1] != cmp2[1]:
                    a.append('Publication')
                if cmp1[2] != cmp2[2]:
                    a.append('DateOfPublication')
                if cmp1[3] != cmp2[3]:
                    a.append('Description')
                if cmp1[4] != cmp2[4]:
                    a.append('LinkToPaper')
                if cmp1[5] != cmp2[5]:
                    a.append('Description')
                if cmp1[6] != cmp2[6]:
                    a.append('PaperId')
                if cmp1[7] != cmp2[7]:
                    a.append('Screenshot')
                if cmp1[8] != cmp2[8]:
                    a.append('Teacher')
                if len(a) != 2:
                    researchpaper[student.Sap_Id].append(a)

    hackathon = {}
    for student in StudentProfile.objects.all():
        hackathon[student.Sap_Id] = []
        for hack in student.hackathon.all():
            a = []
            a.append(hack)
            cmp1 = []
            cmp2 = []
            count = 0
            c1 = hack.history.all().count()
            if c1 == 1:
                break
            for x in hack.history.all():
                b = x.history_date
                k = HistoricalHackathon.objects.get(history_date=b)
                if count == 0:
                    a.append(b)
                    cmp1.append(k.CompetitionName)
                    cmp1.append(k.StartDate)
                    cmp1.append(k.Desc)
                    cmp1.append(k.URL)
                    cmp1.append(k.image1)
                if count == 1:
                    cmp2.append(k.CompetitionName)
                    cmp2.append(k.StartDate)
                    cmp2.append(k.Desc)
                    cmp2.append(k.URL)
                    cmp2.append(k.image1)
                if count == 2:
                    break
                count = count + 1
            if cmp1[0] != cmp2[0]:
                a.append('Competition Name')
            if cmp1[1] != cmp2[1]:
                a.append('Date')
            if cmp1[2] != cmp2[2]:
                a.append('Description')
            if cmp1[3] != cmp2[3]:
                a.append('URL')
            if cmp1[4] != cmp2[4]:
                a.append('Image')
            if len(a) != 2:
                hackathon[student.Sap_Id].append(a)

    education = {}
    for student in StudentProfile.objects.all():
        education[student.Sap_Id] = []
        for edu in student.education.all():
            a = []
            a.append(edu)
            cmp1 = []
            cmp2 = []
            count = 0
            c1 = edu.history.all().count()
            if c1 == 1:
                break
            for x in edu.history.all():
                b = x.history_date
                k = HistoricalEducation.objects.get(history_date=b)
                if count == 0:
                    a.append(b)
                    cmp1.append(k.sem1_gpa)
                    cmp1.append(k.sem2_gpa)
                    cmp1.append(k.sem3_gpa)
                    cmp1.append(k.sem4_gpa)
                    cmp1.append(k.sem5_gpa)
                    cmp1.append(k.sem6_gpa)
                    cmp1.append(k.sem7_gpa)
                    cmp1.append(k.sem8_gpa)
                if count == 1:
                    cmp2.append(k.sem1_gpa)
                    cmp2.append(k.sem2_gpa)
                    cmp2.append(k.sem3_gpa)
                    cmp2.append(k.sem4_gpa)
                    cmp2.append(k.sem5_gpa)
                    cmp2.append(k.sem6_gpa)
                    cmp2.append(k.sem7_gpa)
                    cmp2.append(k.sem8_gpa)
                if count == 2:
                    break
                count = count + 1
            if cmp1[0] != cmp2[0]:
                a.append('Sem 1 Cgpa')
            if cmp1[1] != cmp2[1]:
                a.append('Sem 2 Cgpa')
            if cmp1[2] != cmp2[2]:
                a.append('Sem 3 Cgpa')
            if cmp1[3] != cmp2[3]:
                a.append('Sem 4 Cgpa')
            if cmp1[4] != cmp2[4]:
                a.append('Sem 5 Cgpa')
            if cmp1[5] != cmp2[5]:
                a.append('Sem 6 Cgpa')
            if cmp1[6] != cmp2[6]:
                a.append('Sem 7 Cgpa')
            if cmp1[7] != cmp2[7]:
                a.append('Sem 8 Cgpa')
            if len(a) != 2:
                education[student.Sap_Id].append(a)

    extra = {}
    for student in StudentProfile.objects.all():
        extra[student.Sap_Id] = []
        for ex in student.extracurricular.all():
            a = []
            a.append(ex)
            cmp1 = []
            cmp2 = []
            count = 0
            c1 = ex.history.all().count()
            if c1 == 1:
                break
            for x in ex.history.all():
                b = x.history_date
                k = HistoricalExtraCurricular.objects.get(history_date=b)
                if count == 0:
                    a.append(b)
                    cmp1.append(k.name)
                    cmp1.append(k.desc)
                    cmp1.append(k.achievements)
                    cmp1.append(k.date)
                    cmp1.append(k.Certificate)
                    cmp1.append(k.image1)
                if count == 1:
                    cmp2.append(k.name)
                    cmp2.append(k.desc)
                    cmp2.append(k.achievements)
                    cmp2.append(k.date)
                    cmp2.append(k.Certificate)
                    cmp2.append(k.image1)
                if count == 2:
                    break
                count = count + 1
            if cmp1[0] != cmp2[0]:
                a.append('Name')
            if cmp1[1] != cmp2[1]:
                a.append('Description')
            if cmp1[2] != cmp2[2]:
                a.append('Achievements')
            if cmp1[3] != cmp2[3]:
                a.append('Certificate')
            if cmp1[4] != cmp2[4]:
                a.append('Image')
            if len(a) != 2:
                extra[student.Sap_Id].append(a)
    teacher = TeacherProfile.objects.get(teacher=request.user)
    return render(request, 'user_profile/notifs.html', {'students':stu,'listed': listed, 'projects': projects,
                                                        'beprojects': beprojects, 'education': education,
                                                        'committee': committee, 'hackathon': hackathon,
                                                        'researchpaper': researchpaper, 'extra': extra,
                                                        'teacher': teacher})


def student_list(request):
    try:
        teacher = TeacherProfile.objects.get(teacher=request.user)
    except ObjectDoesNotExist:
        stud = '/login/student/'
        return HttpResponseRedirect(stud)
    most_common_to_take = 3
    skills = Skill.objects.all()
    list_of_skills = [skill.skill for skill in skills]
    most_frequent = collections.Counter(
        list_of_skills).most_common(most_common_to_take)
    skillss = [skill[0] for skill in most_frequent]
    if request.method == 'POST':
        if request.POST.get('start_date'):
            start_date=request.POST.get('start_date')
            last_date=request.POST.get('last_date')
            if start_date and last_date:
                start_date = datetime.strptime(start_date,'%Y-%m-%d')
                last_date = datetime.strptime(last_date,'%Y-%m-%d')
                internship_monthly = Internship.objects.filter(From__range=[start_date,last_date])
                extracurricular_monthly = ExtraCurricular.objects.filter(date__range=[start_date,last_date])
                hackathon_monthly = Hackathon.objects.filter(StartDate__range=[start_date,last_date])
                return render(request, 'user_profile/filter.html', {'internship_monthly': internship_monthly,'hackathon_monthly': hackathon_monthly,'extracurricular_monthly': extracurricular_monthly, 'teacher':TeacherProfile.objects.get(teacher=request.user)})
            else:
                return searchany(request, skillss)
        elif request.POST.get('searchany'):
            return searchany(request, skillss)
        else:
            year = request.POST.getlist('year[]')
            skills = request.POST.getlist('skills[]')
            # gpa = request.POST.getlist('gpa_list[]')

            if year and skills:
                result = StudentProfile.objects.filter(year__in=year).filter(
                    skill__skill__in=skills).distinct()
                projects = Project.objects.filter(
                    skill__skill__in=skills).distinct()
            elif year:
                result = StudentProfile.objects.filter(year__in=year)
                projects = []
            elif skills:
                result = StudentProfile.objects.filter(
                    skill__skill__in=skills).distinct()
                projects = Project.objects.filter(
                    skill__skill__in=skills).distinct()
            else:
                result = []
                projects = []
            return render(request, 'user_profile/filter.html', {'result': result, 'skills': skillss,
                          'projects': projects, 'teacher': teacher})
    else:
        return render(request, 'user_profile/filter.html', {'skills': skillss, 'teacher': teacher})


def average(a):
    if a == []:
        return []
    b = len(list(filter(lambda x: x != 0, a)))
    return float(sum(a) / b) if b != 0 else 0


def teacher_dashboard(request):
    if request.user.is_authenticated:
        try:
            teacher = TeacherProfile.objects.get(teacher=request.user)
        except ObjectDoesNotExist:
            stud = '/login/student/'
            return HttpResponseRedirect(stud)
        if not request.user.is_active:        
            error = 'Your account is disabled. Please activate your account.'
            return render(request, 'user_profile/teacher_login.html', {'error': error})
        context = {}
        context['teacher'] = teacher
        # calculating most common skills
        most_common_to_take = 3
        skills = Skill.objects.all()
        list_of_skills = [skill.skill for skill in skills]
        most_frequent_skills = collections.Counter(
            list_of_skills).most_common(most_common_to_take)
        for i, skill in enumerate(most_frequent_skills):
            context['skill' + str(i + 1)] = skill
        # calculating year-wise internship stats
        internship_objects = Internship.objects.all()
        intern_stats = [
            internship.employee.year for internship in internship_objects]
        intern_stats = collections.Counter(intern_stats)
        context['FE_interns'] = intern_stats['FE']
        context['SE_interns'] = intern_stats['SE']
        context['TE_interns'] = intern_stats['TE']
        context['BE_interns'] = intern_stats['BE']
        # internship line graph
        internship_in_months = []
        context['internship_in_months'] = []
        for internship in internship_objects:
            internship_in_months.append(internship.From.month)
        internship_in_months = collections.Counter(internship_in_months)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        context['months'] = months
        for month in months:
            if months.index(month) + 1 in internship_in_months.keys():
                context['internship_in_months'].append(internship_in_months[months.index(month) + 1])
            else:
                context['internship_in_months'].append(0)
        # list of all pointers
        sem1_list = [education.sem1_gpa for education in Education.objects.all(
        ) if education.sem1_gpa is not None]
        # sem1_list = filter(None, sem1_list)
        sem2_list = [education.sem2_gpa for education in Education.objects.all(
        ) if education.sem2_gpa is not None]
        sem3_list = [education.sem3_gpa for education in Education.objects.all(
        ) if education.sem3_gpa is not None]
        sem4_list = [education.sem4_gpa for education in Education.objects.all(
        ) if education.sem4_gpa is not None]
        sem5_list = [education.sem5_gpa for education in Education.objects.all(
        ) if education.sem5_gpa is not None]
        sem6_list = [education.sem6_gpa for education in Education.objects.all(
        ) if education.sem6_gpa is not None]
        sem7_list = [education.sem7_gpa for education in Education.objects.all(
        ) if education.sem7_gpa is not None]
        sem8_list = [education.sem8_gpa for education in Education.objects.all(
        ) if education.sem8_gpa is not None]
        sem1_list = float(sum(sem1_list) / len(sem1_list)) if len(sem1_list) != 0 else []
        sem2_list = float(sum(sem2_list) / len(sem2_list)) if len(sem2_list) != 0 else []
        sem3_list = float(sum(sem3_list) / len(sem3_list)) if len(sem3_list) != 0 else []
        sem4_list = float(sum(sem4_list) / len(sem4_list)) if len(sem4_list) != 0 else []
        sem5_list = float(sum(sem5_list) / len(sem5_list)) if len(sem5_list) != 0 else []
        sem6_list = float(sum(sem6_list) / len(sem6_list)) if len(sem6_list) != 0 else []
        sem7_list = float(sum(sem7_list) / len(sem7_list)) if len(sem7_list) != 0 else []
        sem8_list = float(sum(sem8_list) / len(sem8_list)) if len(sem8_list) != 0 else []
        context['avg_gpa'] = [sem1_list, sem2_list, sem3_list, sem4_list, sem5_list, sem6_list, sem7_list, sem8_list]
        context['sem_labels'] = ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4', 'Sem 5', 'Sem 6', 'Sem 7', 'Sem 8']
        # batch wise pointers
        FE_gpa_objects = Education.objects.filter(student_profile__year='FE')
        SE_gpa_objects = Education.objects.filter(student_profile__year='SE')
        TE_gpa_objects = Education.objects.filter(student_profile__year='TE')
        BE_gpa_objects = Education.objects.filter(student_profile__year='BE')
        FE_gpa = {'sem1': [], 'sem2': []}
        SE_gpa = {'sem1': [], 'sem2': [], 'sem3': [], 'sem4': []}
        TE_gpa = {'sem1': [], 'sem2': [], 'sem3': [], 'sem4': [], 'sem5': [], 'sem6': []}
        BE_gpa = {'sem1': [], 'sem2': [], 'sem3': [], 'sem4': [], 'sem5': [], 'sem6': [], 'sem7': [], 'sem8': []}
        for edu in FE_gpa_objects:
            FE_gpa['sem1'].append(edu.sem1_gpa if edu.sem1_gpa is not None else 0)
            FE_gpa['sem2'].append(edu.sem2_gpa if edu.sem2_gpa is not None else 0)
        for edu in SE_gpa_objects:
            SE_gpa['sem1'].append(edu.sem1_gpa if edu.sem1_gpa is not None else 0)
            SE_gpa['sem2'].append(edu.sem2_gpa if edu.sem2_gpa is not None else 0)
            SE_gpa['sem3'].append(edu.sem3_gpa if edu.sem3_gpa is not None else 0)
            SE_gpa['sem4'].append(edu.sem4_gpa if edu.sem4_gpa is not None else 0)
        for edu in TE_gpa_objects:
            TE_gpa['sem1'].append(edu.sem1_gpa if edu.sem1_gpa is not None else 0)
            TE_gpa['sem2'].append(edu.sem2_gpa if edu.sem2_gpa is not None else 0)
            TE_gpa['sem3'].append(edu.sem3_gpa if edu.sem3_gpa is not None else 0)
            TE_gpa['sem4'].append(edu.sem4_gpa if edu.sem4_gpa is not None else 0)
            TE_gpa['sem5'].append(edu.sem5_gpa if edu.sem5_gpa is not None else 0)
            TE_gpa['sem6'].append(edu.sem6_gpa if edu.sem6_gpa is not None else 0)
        for edu in BE_gpa_objects:
            BE_gpa['sem1'].append(edu.sem1_gpa if edu.sem1_gpa is not None else 0)
            BE_gpa['sem2'].append(edu.sem2_gpa if edu.sem2_gpa is not None else 0)
            BE_gpa['sem3'].append(edu.sem3_gpa if edu.sem3_gpa is not None else 0)
            BE_gpa['sem4'].append(edu.sem4_gpa if edu.sem4_gpa is not None else 0)
            BE_gpa['sem5'].append(edu.sem5_gpa if edu.sem5_gpa is not None else 0)
            BE_gpa['sem6'].append(edu.sem6_gpa if edu.sem6_gpa is not None else 0)
            BE_gpa['sem7'].append(edu.sem7_gpa if edu.sem7_gpa is not None else 0)
            BE_gpa['sem8'].append(edu.sem8_gpa if edu.sem8_gpa is not None else 0)
        # there's probably a better way to do this
        context['FE_gpa'] = [average(FE_gpa['sem1']), average(FE_gpa['sem2'])]
        context['SE_gpa'] = [average(SE_gpa['sem1']), average(SE_gpa['sem2']),
                            average(SE_gpa['sem3']), average(SE_gpa['sem4'])]
        context['TE_gpa'] = [average(TE_gpa['sem1']), average(TE_gpa['sem2']),
                            average(TE_gpa['sem3']), average(TE_gpa['sem4']),
                            average(TE_gpa['sem5']), average(TE_gpa['sem6'])]
        context['BE_gpa'] = [average(BE_gpa['sem1']), average(BE_gpa['sem2']),
                            average(BE_gpa['sem3']), average(BE_gpa['sem4']),
                            average(BE_gpa['sem5']), average(BE_gpa['sem6']),
                            average(BE_gpa['sem7']), average(BE_gpa['sem8'])]
        # internship time stamps
        intern_dates = [format(internship.From, 'U')
                        for internship in Internship.objects.all()]
        intern_dates.sort()
        # intern_date = [int(x) - int(intern_dates[0]) for x in intern_dates]
        total_regs = StudentProfile.objects.all().count()
        total_intern = Internship.objects.all().count()
        cgpa1 = [pointer.cgpa for pointer in StudentProfile.objects.all(
        ) if pointer.cgpa is not None]
        context['total_regs'] = total_regs
        cgpa1 = float(sum(cgpa1) / len(cgpa1)) if len(cgpa1) != 0 else 0
        context['cgpa1'] = cgpa1
        context['total_intern'] = total_intern
        kt = KT.objects.all().count()
        if total_regs !=0:
            kt_perc = (float)((kt * 100) / total_regs)
        else:
            kt_perc=0
        context['kt_perc'] = round(kt_perc, 2)
        # return HttpResponse(intern_stats)
        return render(request, 'user_profile/teacherprofile.html', context)
    return HttpResponseRedirect('/login/teacher/')


def education_graphs():
    pass


def internship(request, internshipid):
    internship = Internship.objects.get(id=internshipid)
    return render(request, 'user_profile/internship.html', {'intern': internship})


def hackathon(request, hackathonid):
    hackathon = Hackathon.objects.get(id=hackathonid)
    return render(request, 'user_profile/hackathon.html', {'intern': hackathon})


def project(request, projectid):
    project = Project.objects.get(id=projectid)
    return render(request, 'user_profile/project.html', {'intern': project})


def beproject(request, beprojectid):
    beproject = BeProject.objects.get(id=beprojectid)
    return render(request, 'user_profile/beproject.html', {'intern': beproject})


def committee(request, committeeid):
    intern = Committee.objects.get(id=committeeid)
    return render(request, 'user_profile/committee.html', {'intern': intern})


def researchpaper(request, researchpaperid):
    intern = ResearchPaper.objects.get(id=researchpaperid)
    return render(request, 'user_profile/researchpaper.html', {'intern': intern})


def extracurricular(request, extracurricularid):
    intern = ExtraCurricular.objects.get(id=extracurricularid)
    return render(request, 'user_profile/extracurricular.html', {'intern': intern})


def show_edit_studentprofile(request):
    if request.user.is_authenticated:
        try:
            teacher = TeacherProfile.objects.get(teacher=request.user)
            teacher_profile_url = '/teacherdashboard/'
            return HttpResponseRedirect(teacher_profile_url)
        except ObjectDoesNotExist:
            student_profile = StudentProfile.objects.get(student=request.user)
            hackathon = Hackathon.objects.filter(student_profile=student_profile)
            project = Project.objects.filter(student_profile=student_profile)
            committee = Committee.objects.filter(employee=student_profile)
            researchpaper = ResearchPaper.objects.filter(student=student_profile)
            internship = Internship.objects.filter(employee=student_profile)
            admit = Admit.objects.filter(student=student_profile)
            try:
                beproject = BeProject.objects.get(student=student_profile)
            except ObjectDoesNotExist:
                beproject = BeProject.objects.create(student=student_profile)
            try:
                acads = Education.objects.get(student_profile=student_profile)
            except ObjectDoesNotExist:
                acads = Education.objects.create(student_profile=student_profile)
            try:
                competitive_exam = CompetitiveExams.objects.get(student=student_profile)
            except ObjectDoesNotExist:
                competitive_exam = CompetitiveExams.objects.create(student=student_profile)
            if not acads.sem1_tt1:
                t = TermTest.objects.create(tt_name='sem1_tt1')
                for subj in Subject.objects.filter(sem='SEM1'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem1_tt1 = t
                acads.save()
            if not acads.sem1_tt2:
                t = TermTest.objects.create(tt_name='sem1_tt2')
                for subj in Subject.objects.filter(sem='SEM1'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem1_tt2 = t
                acads.save()
            if not acads.sem2_tt1:
                t = TermTest.objects.create(tt_name='sem2_tt1')
                for subj in Subject.objects.filter(sem='SEM2'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem2_tt1 = t
                acads.save()
            if not acads.sem2_tt2:
                t = TermTest.objects.create(tt_name='sem2_tt2')
                for subj in Subject.objects.filter(sem='SEM2'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem2_tt2 = t
                acads.save()
            if not acads.sem3_tt1:
                t = TermTest.objects.create(tt_name='sem3_tt1')
                for subj in Subject.objects.filter(sem='SEM3'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem3_tt1 = t
                acads.save()
            if not acads.sem3_tt2:
                t = TermTest.objects.create(tt_name='sem3_tt2')
                for subj in Subject.objects.filter(sem='SEM3'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem3_tt2 = t
                acads.save()
            if not acads.sem4_tt1:
                t = TermTest.objects.create(tt_name='sem4_tt1')
                for subj in Subject.objects.filter(sem='SEM4'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem4_tt1 = t
                acads.save()
            if not acads.sem4_tt2:
                t = TermTest.objects.create(tt_name='sem4_tt2')
                for subj in Subject.objects.filter(sem='SEM4'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem4_tt2 = t
                acads.save()
            if not acads.sem5_tt1:
                t = TermTest.objects.create(tt_name='sem5_tt1')
                for subj in Subject.objects.filter(sem='SEM5'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem5_tt1 = t
                acads.save()
            if not acads.sem5_tt2:
                t = TermTest.objects.create(tt_name='sem5_tt2')
                for subj in Subject.objects.filter(sem='SEM5'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem5_tt2 = t
                acads.save()
            if not acads.sem6_tt1:
                t = TermTest.objects.create(tt_name='sem6_tt1')
                for subj in Subject.objects.filter(sem='SEM6'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem6_tt1 = t
                acads.save()
            if not acads.sem6_tt2:
                t = TermTest.objects.create(tt_name='sem6_tt2')
                for subj in Subject.objects.filter(sem='SEM6'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem6_tt2 = t
                acads.save()
            if not acads.sem7_tt1:
                t = TermTest.objects.create(tt_name='sem7_tt1')
                for subj in Subject.objects.filter(sem='SEM7'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem7_tt1 = t
                acads.save()
            if not acads.sem7_tt2:
                t = TermTest.objects.create(tt_name='sem7_tt2')
                for subj in Subject.objects.filter(sem='SEM7'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem7_tt2 = t
                acads.save()
            if not acads.sem8_tt1:
                t = TermTest.objects.create(tt_name='sem8_tt1')
                for subj in Subject.objects.filter(sem='SEM8'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem8_tt1 = t
                acads.save()
            if not acads.sem8_tt2:
                t = TermTest.objects.create(tt_name='sem8_tt2')
                for subj in Subject.objects.filter(sem='SEM8'):
                    s = SubjectMarks()
                    s.tt = t
                    s.subject = subj
                    s.save()
                acads.sem8_tt2 = t
                acads.save()
            skill = Skill.objects.filter(user_profile=student_profile)
            skill_list = []
            for s in skill:
                if s.skill != '':
                    skill_list.append(s)
            context = {'student_profile': student_profile, 'hackathon_list': hackathon, 'project_list': project,
                       'committee_list': committee, 'beproject': beproject, 'researchpaper_list': researchpaper,
                       'internship_list': internship, 'acads': acads, 'skill_list': skill_list,
                       'competitive_exam':competitive_exam, 'admit':admit}
            return render(request, 'user_profile/edit_student_profile_2.html', context)
        else:
            return HttpResponseRedirect('/login/student/')


def edit_competitive_exams(request, id):
    if request.method == 'POST':
        student_profile = StudentProfile.objects.get(id=id)
        try:
            competitive_exam = CompetitiveExams.objects.get(student=student_profile)
        except:
            competitive_exam = CompetitiveExams.objects.create(student=student_profile)
        competitive_exam.gre_score = request.POST.get('gre_score')
        competitive_exam.cat_score = request.POST.get('cat_score')
        competitive_exam.gate_score = request.POST.get('gate_score')
        competitive_exam.gmat_score = request.POST.get('gmat_score')
        competitive_exam.toefl_score = request.FILES.get('toefl_score')
        competitive_exam.mhcet_score = request.POST.get('mhcet_score')
        competitive_exam.save()
        return HttpResponse('done')


def edit_basic_info(request, id):
    if request.method == 'POST':
        student_profile = StudentProfile.objects.get(id=id)
        student_profile.first_name = request.POST.get('fname')
        student_profile.last_name = request.POST.get('lname')
        student_profile.department = request.POST.get('department')
        # print(request.POST.get('gender'))
        if (request.POST.get('gender') is not None):
            student_profile.gender = request.POST.get('gender')
        if (request.POST.get('year') is not None):
            student_profile.year = request.POST.get('year')
        student_profile.mobileNo = request.POST.get('mobileNo')
        student_profile.photo = request.FILES.get('photo')
        student_profile.cgpa = request.POST.get('cgpa')
        student_profile.save()
        return HttpResponse('done')


def edit_academic_info(request, id):
    if request.method == 'POST':
        student_profile = StudentProfile.objects.get(id=id)
        try:
            education = Education.objects.get(student_profile=student_profile)
        except ObjectDoesNotExist:
            education = Education.objects.create(student_profile=student_profile)
        print(request.POST)
        if ((request.POST.get('sem1_gpa')) != ''):
            education.sem1_gpa = request.POST.get('sem1_gpa')
        if ((request.POST.get('sem2_gpa')) != ''):
            education.sem2_gpa = request.POST.get('sem2_gpa')
        if ((request.POST.get('sem3_gpa')) != ''):
            education.sem3_gpa = request.POST.get('sem3_gpa')
        if ((request.POST.get('sem4_gpa')) != ''):
            education.sem4_gpa = request.POST.get('sem4_gpa')
        if ((request.POST.get('sem5_gpa')) != ''):
            education.sem5_gpa = request.POST.get('sem5_gpa')
        if ((request.POST.get('sem6_gpa')) != ''):
            education.sem6_gpa = request.POST.get('sem6_gpa')
        if ((request.POST.get('sem7_gpa')) != ''):
            education.sem7_gpa = request.POST.get('sem7_gpa')
        if ((request.POST.get('sem8_gpa')) != ''):
            education.sem8_gpa = request.POST.get('sem8_gpa')
        for subj in education.sem1_tt1.subject.all():
            marks = request.POST.get('sem1_tt1_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem1_tt2.subject.all():
            marks = request.POST.get('sem1_tt2_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem2_tt1.subject.all():
            marks = request.POST.get('sem2_tt1_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem2_tt2.subject.all():
            marks = request.POST.get('sem2_tt2_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem3_tt1.subject.all():
            marks = request.POST.get('sem3_tt1_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem3_tt2.subject.all():
            marks = request.POST.get('sem3_tt2_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem4_tt1.subject.all():
            marks = request.POST.get('sem4_tt1_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem4_tt2.subject.all():
            marks = request.POST.get('sem4_tt2_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem5_tt1.subject.all():
            marks = request.POST.get('sem5_tt1_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem5_tt2.subject.all():
            marks = request.POST.get('sem5_tt2_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem6_tt1.subject.all():
            marks = request.POST.get('sem6_tt1_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem6_tt2.subject.all():
            marks = request.POST.get('sem6_tt2_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem7_tt1.subject.all():
            marks = request.POST.get('sem7_tt1_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem7_tt2.subject.all():
            marks = request.POST.get('sem7_tt2_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem8_tt1.subject.all():
            marks = request.POST.get('sem8_tt1_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        for subj in education.sem8_tt2.subject.all():
            marks = request.POST.get('sem8_tt2_' + str(subj.subject.name))
            if marks != '':
                subj.marks = marks
                print(subj)
                subj.save()
        student_profile.subject_semester = request.POST.get('kt')
        education.save()
        return HttpResponse('done')


def edit_skill_info(request, id):
    if request.method == 'POST':
        student_profile = StudentProfile.objects.get(id=id)
        skill = Skill.objects.create(user_profile=student_profile)
        skill.skill = request.POST.get('skill')
        # print(request.POST.get('skill'))
        skill.save()
        # print('.....')
        return HttpResponseRedirect('')
    else:
        data = Skill.objects.last()
        return JsonResponse({"skill": data.skill, "id": data.id})


def edit_hackathon_info(request, id):
    if request.method == 'POST':
        print(request.POST)
        print(request.FILES)
        student_profile = StudentProfile.objects.get(id=id)
        hackathon = Hackathon.objects.create(student_profile=student_profile)
        # hackathon = Hackathon.objects.get(student_profile_id=id)
        hackathon.CompetitionName = request.POST.get('HackathonName')
        if request.POST.get('HackathonDate') != '':
            hackathon.StartDate = request.POST.get('HackathonDate')
        hackathon.Desc = request.POST.get('HackathonDescription')
        hackathon.URL = request.POST.get('HackathonUrl')
        hackathon.image1 = request.FILES.get('image1')
        hackathon.image2 = request.FILES.get('image2')
        hackathon.image3 = request.FILES.get('image3')
        hackathon.image4 = request.FILES.get('image4')
        hackathon.image5 = request.FILES.get('image5')
        hackathon.save()
        # number = "9833175929"
        # message = "THE STUDENT " + str(student_profile.first_name) + " has added the Hackathon " \
        #     + hackathon.CompetitionName + " to his profile"
        # send_sms(message, number)
        # print("sdsdsdsd")
        return HttpResponseRedirect('')
    else:
        data = Hackathon.objects.last()
        return JsonResponse({"CompetitionName": data.CompetitionName, "Date": data.StartDate, "Desc": data.Desc,
                             "id": data.id, "url": data.URL})


def edit_project_info(request, id):
    if request.method == 'POST':
        student_profile = StudentProfile.objects.get(id=id)
        project = Project.objects.create(student_profile=student_profile)
        skill = Skill.objects.create(user_profile=student_profile)
        skill.skill = request.POST.get('ProjectSkill')
        project.ProjURL = request.POST.get('ProjectUrl')
        project.ProjName = request.POST.get('ProjectName')
        project.ProjDesc = request.POST.get('ProjectDescription')
        project.image1 = request.FILES.get('image1')
        project.image2 = request.FILES.get('image2')
        project.image3 = request.FILES.get('image3')
        project.image4 = request.FILES.get('image4')
        project.image5 = request.FILES.get('image5')
        project.skill = skill
        project.save()
        skill.save()
        return HttpResponse('done')
    else:
        data = Project.objects.last()
        return JsonResponse({"ProjName": data.ProjName, "ProjURL": data.ProjURL, "ProjDesc": data.ProjDesc,
                             "id": data.id, "Skill": data.skill.skill})


def edit_internship_info(request, id):
    if request.method == 'POST':
        student_profile = StudentProfile.objects.get(id=id)
        internship = Internship.objects.create(employee=student_profile)
        print("HI")
        internship.company = request.POST.get('InternshipName')
        internship.stipend = request.POST.get('stipend')
        print(request.POST.get('InternshipName'))
        internship.desc = request.POST.get('InternshipDescription')
        print(request.POST.get('InternshipDescription'))
        internship.Position = request.POST.get('InternshipPosition')
        internship.Loc = request.POST.get('InternshipLocation')
        if request.POST.get('InternshipFrom') != '':
            internship.From = request.POST.get('InternshipFrom')
        if request.POST.get('InternshipTo') != '':
            internship.To = request.POST.get('InternshipTo')
        internship.Certificate = request.FILES.get('certificate')
        internship.image1 = request.FILES.get('image1')
        internship.image2 = request.FILES.get('image2')
        internship.image3 = request.FILES.get('image3')
        internship.image4 = request.FILES.get('image4')
        internship.image5 = request.FILES.get('image5')
        internship.save()
        print(internship.company)
        return HttpResponse('done')
    else:
        data = Internship.objects.last()
        return JsonResponse({"company": data.company, "Position": data.Position, "desc": data.desc, "Loc": data.Loc,
                             "From": data.From, "To": data.To, "id": data.id})


def edit_committee_info(request, id):
    if request.method == 'POST':
        student_profile = StudentProfile.objects.get(id=id)
        committee = Committee.objects.create(employee=student_profile)
        print("HI")
        committee.OrganisationName = request.POST.get('CommitteeName')
        print(request.POST.get('CommitteeName'))
        committee.YourPosition = request.POST.get('CommitteePosition')
        committee.Desc = request.POST.get('CommitteeDescription')
        committee.Loc = request.POST.get('CommitteeLocation')
        if request.POST.get('CommitteeFrom') != '':
            committee.dateFrom = request.POST.get('CommitteeFrom')
        if request.POST.get('CommitteeTo') != '':
            committee.dateTo = request.POST.get('CommitteeTo')
        committee.Certificate = request.FILES.get('certificate')
        committee.image1 = request.FILES.get('image1')
        committee.image2 = request.FILES.get('image2')
        committee.image3 = request.FILES.get('image3')
        committee.image4 = request.FILES.get('image4')
        committee.image5 = request.FILES.get('image5')
        print("Yo")
        committee.save()
        return HttpResponse('done')
    else:
        data = Committee.objects.last()
        return JsonResponse({"OrganisationName": data.OrganisationName, "YourPosition": data.YourPosition,
                             "Desc": data.Desc, "Loc": data.Loc, "dateFrom": data.dateFrom, "dateTo": data.dateTo,
                             "id": data.id})


def edit_research_paper_info(request, id):
    if request.method == 'POST':
        print("aayush")
        student_profile = StudentProfile.objects.get(id=id)
        paper = ResearchPaper.objects.create(student=student_profile)
        paper.Title = request.POST.get('ResearchPaperName')
        paper.Publication = request.POST.get('ResearchPaperPublication')
        paper.Desc = request.POST.get('ResearchPaperDescription')
        paper.isbn = request.POST.get('isbn')
        paper.status = request.POST.get('status')
        paper.LinkToPaper = request.POST.get('ResearchPaperUrl')
        paper.image1 = request.FILES.get('image1')
        paper.image2 = request.FILES.get('image2')
        paper.image3 = request.FILES.get('image3')
        paper.image4 = request.FILES.get('image4')
        paper.image5 = request.FILES.get('image5')
        paper.save()
        print(paper.status)
        return HttpResponse('done')
    else:
        data = ResearchPaper.objects.last()
        return JsonResponse({"Title": data.Title, "Publication": data.Publication,
                             "DateOfPublication": data.DateOfPublication, "Desc": data.Desc,
                             "LinkToPaper": data.LinkToPaper, "id": data.id})


def edit_extra_info(request, id):
    if request.method == 'POST':
        student_profile = StudentProfile.objects.get(id=id)
        extra = ExtraCurricular.objects.create(student=student_profile)
        extra.name = request.POST.get('ExtraName')
        extra.desc = request.POST.get('ExtraDescription')
        extra.achievements = request.POST.get('ExtraAchievements')
        if request.POST.get('ExtraDate') != '':
            extra.date = request.POST.get('ExtraDate')
        extra.Certificate = request.FILES.get('certificate')
        extra.image1 = request.FILES.get('image1')
        extra.image2 = request.FILES.get('image2')
        extra.image3 = request.FILES.get('image3')
        extra.image4 = request.FILES.get('image4')
        extra.image5 = request.FILES.get('image5')
        extra.save()
        return HttpResponse('done')
    else:
        data = ExtraCurricular.objects.last()
        return JsonResponse({"name": data.name, "desc": data.desc,
                             "achievements": data.achievements, "date": data.date,
                             "id": data.id})


def edit_beproject_info(request, id):
    if request.method == 'POST':
        student_profile = StudentProfile.objects.get(id=id)
        try:
            proj = BeProject.objects.get(student=student_profile)
        except ObjectDoesNotExist:
            proj = BeProject.objects.create(student=student_profile)
        proj.ProjName = request.POST.get('BEProjectName')
        proj.ProjURL = request.POST.get('BEProjectUrl')
        proj.ProjDesc = request.POST.get('BEProjectDescription')
        proj.image1 = request.FILES.get('image1')
        proj.image2 = request.FILES.get('image2')
        proj.image3 = request.FILES.get('image3')
        proj.image4 = request.FILES.get('image4')
        proj.image5 = request.FILES.get('image5')
        proj.project_report = request.FILES.get('project_report')
        proj.save()
        return HttpResponse('done')

def edit_admit_info(request, id):
    if request.method == 'POST':
        student_profile = StudentProfile.objects.get(id=id)
        extra = Admit.objects.create(student=student_profile)
        extra.college_name = request.POST.get('college_name')
        extra.masters_field = request.POST.get('masters_field')
        extra.college_location = request.POST.get('college_location')
        extra.selected = request.POST.get('selected')
        extra.save()
        return HttpResponse('done')
    else:
        data = Admit.objects.last()
        return JsonResponse({"college_name": data.college_name, "masters_field": data.masters_field,
                             "college_location": data.college_location, "selected": data.selected,
                             "id": data.id})


def delete_hackathon_info(request, id):
        hackathon = Hackathon.objects.get(id=id)
        hackathon.delete()
        return HttpResponseRedirect('/editprofile/')


def delete_project_info(request, id):
        project = Project.objects.get(id=id)
        skill = project.skill
        project.delete()
        skill.delete()
        return HttpResponseRedirect('/editprofile/')


def delete_committee_info(request, id):
        committee = Committee.objects.get(id=id)
        committee.delete()
        return HttpResponseRedirect('/editprofile/')


def delete_internship_info(request, id):
        internship = Internship.objects.get(id=id)
        internship.delete()
        return HttpResponseRedirect('/editprofile/')


def delete_researchpaper_info(request, id):
        researchpaper = ResearchPaper.objects.get(id=id)
        researchpaper.delete()
        return HttpResponseRedirect('/editprofile/')


def delete_skill_info(request, id):
        skill = Skill.objects.get(id=id)
        skill.delete()
        return HttpResponseRedirect('/editprofile/')


def delete_extra_info(request, id):
        extra = ExtraCurricular.objects.get(id=id)
        extra.delete()
        return HttpResponseRedirect('/editprofile/')

def delete_admit_info(request, id):
        extra = Admit.objects.get(id=id)
        extra.delete()
        return HttpResponseRedirect('/editprofile/')


def send_sms(message, number):
    print(number)
    key = os.environ['MSG91KEY'].strip()
    print(key)
    urltosend = 'http://api.msg91.com/api/sendhttp.php?authkey=' + key + '&mobiles=' + number + '&message=' \
        + message + '&sender=MSGIND&route=4'
    print(urltosend)
    r = requests.get(urltosend)
    print(r.status_code)
    '''
    Adding instructions because I will forget later
    Environment variables will not directly work with virtual environments.
    #
    To make them work, in the file [yourvirtualenvname]/bin/activate add the following line :
    #
    export MSG91KEY="YOURKEYHERE"
    #
    And also remember, rudresh is the best (DUH)
    '''

def filters_adv(request):
    internship = Internship.objects.all()
    projects = Project.objects.all()
    committe = Committee.objects.all()
    researchpaper = ResearchPaper.objects.all()
    beproj = BeProject.objects.all()
    hackathon = Hackathon.objects.all()
    extracurricular = ExtraCurricular.objects.all()
    user = request.user
    logedin_user = TeacherProfile.objects.get(teacher=user)

    return render(request, 'user_profile/filter_adv.html',
                  {'internship': internship, 'projects': projects, 'committe': committe,
                   'researchpaper': researchpaper, 'beproj': beproj, 'logedin_user':logedin_user,
                   'hackathon': hackathon, 'extracurricular': extracurricular})
